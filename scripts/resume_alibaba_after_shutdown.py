"""Resume the interrupted formal Alibaba calibration without changing science.

This execution-only wrapper preserves every audited trajectory, launches the
original two joint-DAG workers (which skip existing exact output keys), audits
the completed matrix, freezes the Alibaba selection, and resumes the already
approved downstream queue.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT, save_json
from core.status import save_execution_status
from scripts.audit_alibaba_shutdown_recovery import audit_results
from scripts.formal_parallel import alibaba_diagnostic_jobs, run_parallel_phase
from scripts.run_all_final import command, update_report
from scripts.run_calibration_joint_dag_parallel import aggregate_and_freeze


EXPECTED = 48_600
PRESERVED = 28_755
RECOVERY = 19_845
WORKERS = 2
QUEUE_AFTER_CALIBRATION = ["Alibaba diagnostic", "bootstrap/final aggregation", "P15", "P16"]
EXPECTED_HASHES = {
    "core/engine.py": "b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6",
    "core/models.py": "b38b29b74ff4191add5e8c48e9d916529afb67f801830c68e290f07deacfa656",
    "core/protocol.py": "48254f026a096767271ef784e5ed22f8b24ab3369bf3614a8e23c80b626eff15",
    "core/joint_dag.py": "9020dc8cced08766c0bb02e5103578e3da958d02c2f504f793e4d3ebda76374a",
    "configs/frozen_candidate_config.yaml": "4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea",
    "configs/frozen_commit_config.yaml": "1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a",
    "configs/frozen_baseline_config.yaml": "765f58a595a156320caa3c4664657670968d4638e5bf15b7d430444b82581908",
    "configs/calibration_protocol.yaml": "e08902bbf8edefe975b8f55be5d3aeda0dcbe033326c40f6d1dcfd9b6aa6b461",
    "pool_manifest.json": "f5550a641384625746ec8fd36791c37e00be5610ed67097c1c5ec69d722ee8fe",
    "alibaba_pool_manifest.json": "55918806ab6b71d206a944415465d449a2d0463a5befaa8adb06c90508df5d89",
    "scripts/run_calibration_joint_dag.py": "c3e32d9fc149c0f6188b992b0448e6e76bda66bc8b1ea5c4b922ee9eec4189ea",
    "scripts/run_calibration_joint_dag_parallel.py": "9e52c872e875a5b174bf699ae16e4dbfa8565e3c42cbe06552d6a8d596dc66fb",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def result_count() -> int:
    return sum(1 for _ in (ROOT / "results" / "alibaba_calibration").glob("policy*.csv"))


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def preflight() -> dict:
    mismatches = {name: {"expected": expected, "actual": sha256(ROOT / name)}
                  for name, expected in EXPECTED_HASHES.items() if sha256(ROOT / name) != expected}
    integrity = load_json("audits/alibaba_shutdown_recovery_integrity.json")
    cache = load_json("audits/alibaba_shutdown_cache_recovery.json")
    equivalence = load_json("audits/alibaba_calibration_resume_equivalence.json")
    implementation = load_json("audits/alibaba_joint_dag_implementation.json")
    checks = {
        "all_frozen_scientific_hashes_match": not mismatches,
        "result_integrity_pass": integrity.get("status") == "passed",
        "valid_preserved_exact": integrity.get("valid_completed_keys") == PRESERVED,
        "recovery_exact": integrity.get("remaining_keys") == RECOVERY,
        "invalid_zero": integrity.get("invalid_or_partial_count") == 0,
        "duplicate_zero": integrity.get("duplicate_key_count") == 0,
        "unexpected_zero": integrity.get("unexpected_key_count") == 0,
        "scientific_hash_mismatch_zero": integrity.get("scientific_hash_mismatch_count") == 0,
        "formal_count_exact": result_count() == PRESERVED,
        "cache_integrity_pass": cache.get("status") == "passed" and cache.get("rejected_or_excluded_artifacts") == 0,
        "resume_equivalence_pass": equivalence.get("status") == "passed" and equivalence.get("max_abs_diff", 1) <= 1e-12,
        "scientific_implementation_unchanged": equivalence.get("scientific_implementation_changed") is False,
        "original_executor_identity": implementation.get("git_sha") == "d6d33075cb3afa55a24878e2343f1bc1d1c9368a",
        "no_legacy_heldout_directory": not (ROOT / "results" / "heldout").exists(),
    }
    report = {
        "status": "passed" if all(checks.values()) else "failed",
        "created_at": datetime.datetime.now().isoformat(),
        "checks": checks,
        "hash_mismatches": mismatches,
        "recovery_executor_commit": git_sha(),
        "scientific_executor_commit": implementation.get("git_sha"),
        "expected": EXPECTED,
        "valid_preserved": PRESERVED,
        "missing": RECOVERY,
        "invalid_rerun": 0,
        "recovery_queue": RECOVERY,
        "cache_preserved": cache.get("accepted_artifacts"),
        "cache_recomputed_for_invalid": 0,
        "scientific_change": False,
    }
    save_json(ROOT / "audits" / "alibaba_shutdown_recovery_preflight.json", report)
    if report["status"] != "passed":
        raise RuntimeError(f"Alibaba recovery preflight failed: {report}")
    return report


def cache_metrics() -> tuple[dict, list]:
    names = ["candidate_l1_hits", "candidate_l2_hits", "candidate_trainings", "candidate_l2_writes",
             "evidence_l1_hits", "evidence_l2_hits", "evidence_computations", "evidence_l2_writes"]
    totals = {name: 0 for name in names}
    states = []
    for worker in range(WORKERS):
        path = ROOT / "logs" / f"alibaba_calibration_worker{worker}.json"
        if path.exists():
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
                states.append(state)
                for name in names:
                    totals[name] += state.get("cache_metrics", {}).get(name, 0)
            except (OSError, json.JSONDecodeError):
                pass
    return totals, states


def run_recovery_workers(pre: dict) -> dict:
    processes = []
    started = time.time()
    for worker in range(WORKERS):
        command_line = [sys.executable, str(ROOT / "scripts" / "run_calibration_joint_dag.py"),
                        "--domain", "alibaba", "--worker-index", str(worker), "--num-workers", str(WORKERS),
                        "--output-name", "alibaba_calibration", "--formal"]
        processes.append(subprocess.Popen(command_line, cwd=ROOT))
    save_json(ROOT / "logs" / "alibaba_shutdown_recovery_launch.json", {
        **pre, "runner_pid": os.getpid(), "worker_pids": [process.pid for process in processes],
        "launched_at": datetime.datetime.now().isoformat(),
    })
    try:
        while True:
            codes = [process.poll() for process in processes]
            completed = result_count()
            new_completed = max(0, completed - PRESERVED)
            elapsed = max(time.time() - started, 1e-9)
            rate = new_completed / elapsed
            metrics, states = cache_metrics()
            save_execution_status(ROOT / "logs" / "execution_status.json", {
                "phase": "Alibaba calibration shutdown recovery",
                "completed_trajectories": completed, "expected_trajectories": EXPECTED,
                "valid_preserved": PRESERVED, "recovery_expected": RECOVERY,
                "newly_completed": new_completed, "remaining_trajectories": EXPECTED - completed,
                "throughput_trajectories_per_hour": rate * 3600,
                "eta_s": (EXPECTED - completed) / rate if rate else None,
                "workers": WORKERS, "worker_pids": [process.pid for process in processes],
                "worker_status": states, "cache_metrics": metrics,
                "scientific_change": False, "recovery_executor_commit": git_sha(),
                "scientific_executor_commit": pre["scientific_executor_commit"],
                "queue_remaining": QUEUE_AFTER_CALIBRATION,
                "updated_at": datetime.datetime.now().isoformat(), "heldout_started": True,
            })
            failed = [(index, code) for index, code in enumerate(codes) if code not in (None, 0)]
            if failed:
                raise RuntimeError(f"Alibaba recovery worker failed: {failed}")
            if all(code == 0 for code in codes):
                break
            time.sleep(15)
    except BaseException:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
        raise
    if result_count() != EXPECTED:
        raise RuntimeError(f"workers exited with {result_count()}/{EXPECTED} outputs")
    metrics, _ = cache_metrics()
    return {"elapsed_s": time.time() - started, "cache_metrics": metrics,
            "worker_pids": [process.pid for process in processes]}


def refresh_executor_freeze() -> None:
    path = ROOT / "audits" / "q3_executor_freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    previous = freeze["git_sha"]
    freeze["pre_shutdown_executor_git_sha"] = previous
    freeze["git_sha"] = git_sha()
    freeze["recovery_note"] = "approved shutdown-recovery orchestration commit; scientific implementation unchanged"
    freeze["recovery_updated_at"] = datetime.datetime.now().isoformat()
    save_json(path, freeze)


def continue_queue() -> None:
    commit_config = json.loads((ROOT / "configs" / "alibaba_frozen_commit_config.yaml").read_text(encoding="utf-8"))
    run_parallel_phase("Q6_Alibaba_diagnostic", alibaba_diagnostic_jobs(commit_config), QUEUE_AFTER_CALIBRATION[1:])
    update_report("P13 Alibaba Q6 完成", "关机恢复后的 calibration、selection/freeze 与完整性审计 PASS；继续冻结队列。")
    command("summarize.py")
    command("derived_metrics.py")
    command("finalize_outputs.py")
    command("finalize_report.py")
    command("final_reproducibility_audit_parallel.py")
    command("finalize_report.py")
    save_execution_status(ROOT / "logs" / "execution_status.json", {
        "phase": "P16 complete", "phase_complete": "P16", "worker_pids": [],
        "heldout_started": True, "git_sha": git_sha(), "remaining": [],
        "completed_at": datetime.datetime.now().isoformat(),
    })
    update_report("P16 完成", "完整正式实验、图表、4,000 次中心聚类 bootstrap 与最终复现审计均已完成。")


def main() -> None:
    lock = ROOT / "logs" / "runner.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    (ROOT / "runner.pid").write_text(str(os.getpid()), encoding="utf-8")
    try:
        pre = preflight()
        update_report("Alibaba calibration 关机恢复已启动",
                      f"保留 {PRESERVED} 条已审计轨迹，只执行 {RECOVERY} 条缺失轨迹；科学实现与冻结协议不变。")
        recovery = run_recovery_workers(pre)
        post = audit_results()
        if not (post.get("status") == "passed" and post.get("valid_completed_keys") == EXPECTED
                and post.get("remaining_keys") == 0 and post.get("invalid_or_partial_count") == 0
                and post.get("duplicate_key_count") == 0 and post.get("unexpected_key_count") == 0
                and post.get("scientific_hash_mismatch_count") == 0):
            raise RuntimeError(f"post-recovery scientific integrity failed: {post}")
        selection, config_hash = aggregate_and_freeze("alibaba")
        completion = {
            "status": "passed", "completed_at": datetime.datetime.now().isoformat(),
            "root_cause": "EXTERNAL_SYSTEM_SHUTDOWN", "expected": EXPECTED,
            "valid_preserved": PRESERVED, "recovered": RECOVERY, "final_valid": EXPECTED,
            "missing": 0, "invalid": 0, "duplicate": 0, "unexpected": 0,
            "scientific_hash_mismatch": 0, "recovery_executor_commit": git_sha(),
            "scientific_executor_commit": pre["scientific_executor_commit"],
            "scientific_change": False, "cache_metrics_during_recovery": recovery["cache_metrics"],
            "recovery_elapsed_s": recovery["elapsed_s"], "selection": selection,
            "alibaba_frozen_commit_config_sha256": config_hash,
        }
        save_json(ROOT / "audits" / "alibaba_calibration_shutdown_recovery_completion.json", completion)
        refresh_executor_freeze()
        update_report("Alibaba calibration 关机恢复完成",
                      f"48600/48600，duplicate/missing/invalid/unexpected 均为 0；配置选择已冻结，SHA-256 `{config_hash}`。")
        continue_queue()
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        save_json(ROOT / "logs" / "execution_failure.json", {
            "time": datetime.datetime.now().isoformat(), "error": error,
            "status": "STOPPED_NO_AUTOMATIC_RETRY", "runner": "resume_alibaba_after_shutdown.py",
        })
        raise
    finally:
        lock.unlink(missing_ok=True)
        (ROOT / "runner.pid").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
