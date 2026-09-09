"""Execution-only two-worker scheduler for post-Q2 formal workloads."""
from __future__ import annotations

import datetime
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from core.protocol import POOLS, ROOT, save_json
from core.status import save_execution_status


METHODS = [
    "Frozen", "Always-FT", "ER", "EWC", "Huber-FT",
    "CLeaR-Predictor", "ValidationCommit", "Proposed", "OracleCommit",
]
WORKERS = 2


def load_frozen_config():
    cfg = {}
    for name in ["frozen_candidate_config.yaml", "frozen_commit_config.yaml", "frozen_baseline_config.yaml"]:
        cfg.update(json.loads((ROOT / "configs" / name).read_text(encoding="utf-8")))
    return cfg


def make_job(output, center, seed, method, kind, alpha, location="both", *, backbone="GRU", H=1,
             key="base", repeat=0, cfg_overrides=None):
    filename = f"{key}_{center}_{seed}_{backbone}_H{H}_{method}_{kind}_{alpha}_{location}_r{repeat}.csv"
    return {
        "output": output, "filename": filename, "center": int(center), "seed": int(seed),
        "method": method, "kind": kind, "alpha": float(alpha), "location": location,
        "backbone": backbone, "H": int(H), "key": key, "repeat": int(repeat),
        "cfg_overrides": cfg_overrides or {}, "stages": 24,
    }


def q4_jobs():
    return [make_job("q4_ablation", c, seed, method, kind, alpha)
            for seed, c, (kind, alpha), method in itertools.product(
                [7311, 7312, 7313], POOLS["heldout"][:10], [("clean", 0.0), ("mixed", 0.1)],
                ["Proposed", "SinglePath", "MeanDelta", "RecentOnly", "MeanVerification", "RobustAlways"])]


def q5_sensitivity_jobs():
    cfg = load_frozen_config()
    variants = [(f"B{b}_beta{beta}", {"B": b, "beta": beta})
                for b, beta in itertools.product([5, 10], [0.1, 0.2])]
    variants += [(f"capacity{capacity}", {"capacity": capacity}) for capacity in [12, 24, 48]]
    for name in ["kappa_rec", "kappa_hist"]:
        for sign in [-1, 1]:
            variants.append((f"{name}_{sign}", {name: max(0.0, cfg.get(name, 1.0) + sign * 0.5)}))
    return [make_job("q5_sensitivity_cost", c, seed, "Proposed", kind, alpha, key=key, cfg_overrides=overrides)
            for seed, c, (kind, alpha), (key, overrides) in itertools.product(
                [7311, 7312, 7313], POOLS["heldout"][:10], [("clean", 0.0), ("mixed", 0.1)], variants)]


def q5_generality_jobs():
    return [make_job("q5_generality", c, seed, method, kind, alpha, backbone=backbone, H=H, key="generality")
            for seed, backbone, H in itertools.product([7311, 7312, 7313], ["MLP", "TCN", "GRU"], [1, 4])
            for c, (kind, alpha), method in itertools.product(
                POOLS["heldout"][:10], [("clean", 0.0), ("mixed", 0.1)],
                ["Frozen", "Always-FT", "ER", "ValidationCommit", "Proposed"])]


def q5_runtime_jobs():
    return [make_job("q5_runtime", c, 7311, method, "mixed", 0.1, key="runtime", repeat=repeat)
            for repeat, c, method in itertools.product(range(5), POOLS["heldout"][:10], METHODS[:-1])]


def alibaba_direct_jobs():
    return [make_job("q6_alibaba", c, seed, method, kind, alpha, key="direct_transfer")
            for seed, c, (kind, alpha), method in itertools.product(
                [7311, 7312, 7313], range(20060, 20100), [("clean", 0.0), ("mixed", 0.1)], METHODS)]


def alibaba_diagnostic_jobs(commit_config):
    overrides = {"retain_all": False, "validation_retain_all": False, **commit_config}
    return [make_job("q6_alibaba", c, seed, method, kind, alpha,
                     key="domain_calibration_diagnostic", cfg_overrides=overrides)
            for seed, c, (kind, alpha), method in itertools.product(
                [7311, 7312, 7313], range(20060, 20100), [("clean", 0.0), ("mixed", 0.1)],
                ["ValidationCommit", "Proposed"])]


def _group_key(job):
    return (job["output"], job["center"], job["seed"], job["kind"], job["alpha"], job["location"],
            job["backbone"], job["H"], job["key"], job["repeat"])


def partition_jobs(jobs, workers=WORKERS):
    """Assign whole lifecycles, keeping related method groups on one worker."""
    groups = []
    for _, group in itertools.groupby(jobs, key=_group_key):
        groups.append(list(group))
    bins = [[] for _ in range(workers)]
    loads = [0] * workers
    for group in groups:
        target = min(range(workers), key=lambda index: loads[index])
        bins[target].extend(group)
        loads[target] += len(group)
    return bins


def write_manifest(phase, jobs, workers=WORKERS):
    assert workers == 2
    assert jobs and len({job["filename"] for job in jobs}) == len(jobs)
    assignments = partition_jobs(jobs, workers)
    assert sorted(job["filename"] for group in assignments for job in group) == sorted(job["filename"] for job in jobs)
    path = ROOT / "audits" / "execution_manifests" / f"{phase}.json"
    save_json(path, {
        "phase": phase, "created_at": datetime.datetime.now().isoformat(), "workers": workers,
        "partition_unit": "complete center x condition x seed x method lifecycle",
        "stages_per_lifecycle": 24, "expected_trajectories": len(jobs),
        "assignments": {str(index): group for index, group in enumerate(assignments)},
    })
    return path


def _valid_file(path, job):
    try:
        frame = pd.read_csv(path)
        return (len(frame) == 24 and frame.stage.tolist() == list(range(1, 25))
                and frame.method.nunique() == 1 and str(frame.method.iloc[0]) == job["method"]
                and frame.center_id.nunique() == 1 and int(frame.center_id.iloc[0]) == job["center"]
                and frame.model_seed.nunique() == 1 and int(frame.model_seed.iloc[0]) == job["seed"]
                and frame.attack_type.nunique() == 1 and str(frame.attack_type.iloc[0]) == job["kind"]
                and frame.attack_location.nunique() == 1 and str(frame.attack_location.iloc[0]) == job["location"])
    except Exception:
        return False


def audit_phase(phase, jobs):
    invalid = []
    missing = []
    for job in jobs:
        path = ROOT / "results" / job["output"] / job["filename"]
        if not path.exists():
            missing.append(job["filename"])
        elif not _valid_file(path, job):
            invalid.append(job["filename"])
    temp_files = sorted(str(path.relative_to(ROOT)) for output in {job["output"] for job in jobs}
                        for path in (ROOT / "results" / output).glob("*.tmp"))
    report = {
        "status": "passed" if not missing and not invalid and not temp_files else "failed",
        "phase": phase, "expected": len(jobs), "completed": len(jobs) - len(missing),
        "missing": missing, "invalid": invalid, "duplicate_manifest_filenames": len(jobs) - len({j["filename"] for j in jobs}),
        "temp_files": temp_files, "stages_per_lifecycle": 24,
    }
    save_json(ROOT / "audits" / f"{phase}_parallel_execution.json", report)
    if report["status"] != "passed":
        raise RuntimeError(report)
    return report


def run_parallel_phase(phase, jobs, queue_remaining=None):
    manifest = write_manifest(phase, jobs)
    processes = []
    started = time.time()
    initial = sum((ROOT / "results" / job["output"] / job["filename"]).exists() for job in jobs)
    for worker in range(WORKERS):
        cmd = [sys.executable, str(ROOT / "scripts" / "formal_workload_worker.py"),
               "--manifest", str(manifest), "--worker", str(worker)]
        processes.append(subprocess.Popen(cmd, cwd=ROOT))
    expected_paths = [ROOT / "results" / job["output"] / job["filename"] for job in jobs]
    last_status = 0.0
    try:
        while True:
            codes = [process.poll() for process in processes]
            now = time.time()
            if now - last_status >= 15 or all(code is not None for code in codes):
                completed = sum(path.exists() for path in expected_paths)
                elapsed = max(now - started, 1e-9)
                new_completed = max(0, completed - initial)
                rate = new_completed / elapsed
                eta = (len(jobs) - completed) / rate if rate else None
                worker_status = []
                for worker in range(WORKERS):
                    path = ROOT / "logs" / f"formal_worker{worker}.json"
                    if path.exists():
                        try: worker_status.append(json.loads(path.read_text(encoding="utf-8")))
                        except Exception: pass
                save_execution_status(ROOT / "logs" / "execution_status.json", {
                    "phase": phase, "completed_trajectories": completed, "expected_trajectories": len(jobs),
                    "newly_completed": new_completed, "elapsed_s": elapsed,
                    "throughput_trajectories_per_hour": rate * 3600, "phase_eta_s": eta,
                    "workers": WORKERS, "worker_pids": [process.pid for process in processes],
                    "partition_unit": "complete center x condition x seed x method lifecycle",
                    "worker_status": worker_status, "queue_remaining": queue_remaining or [],
                    "heldout_started": True, "updated_at": datetime.datetime.now().isoformat(),
                })
                last_status = now
            failed = [(index, code) for index, code in enumerate(codes) if code not in (None, 0)]
            if failed:
                raise RuntimeError(f"{phase} worker failure: {failed}")
            if all(code == 0 for code in codes):
                break
            time.sleep(5)
    except BaseException:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: process.kill()
        raise
    report = audit_phase(phase, jobs)
    save_execution_status(ROOT / "logs" / "execution_status.json", {
        "phase": phase, "phase_complete": phase, "completed_trajectories": len(jobs),
        "expected_trajectories": len(jobs), "workers": WORKERS, "worker_pids": [],
        "queue_remaining": queue_remaining or [], "integrity_audit": "PASS", "heldout_started": True,
        "updated_at": datetime.datetime.now().isoformat(),
    })
    return report
