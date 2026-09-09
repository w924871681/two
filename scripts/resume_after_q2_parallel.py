"""Independent post-Q2 queue using the approved two-worker execution topology."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from core.engine import initial_model
from core.protocol import POOLS, ROOT, save_json
from core.status import save_execution_status
from scripts.executor_switch_freeze import git_sha, require_executor_switch_freeze
from scripts.formal_parallel import (
    alibaba_diagnostic_jobs, alibaba_direct_jobs, q4_jobs, q5_generality_jobs,
    q5_runtime_jobs, q5_sensitivity_jobs, run_parallel_phase,
)
from scripts.pretrain import pretrain
from scripts.run_all_final import command, update_report


QUEUE = ["Q3", "Q4", "Q5 sensitivity", "Q5 generality", "Q5 runtime", "Q6 Alibaba direct",
         "Alibaba calibration", "Alibaba diagnostic", "bootstrap/final aggregation", "P15", "P16"]


def build_q3():
    paths = list((ROOT / "results" / "q1_overall").glob("base_*.csv"))
    assert len(paths) == 1620
    clean_paths = []
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        if float(frame.attack_alpha.iloc[0]) == 0.0:
            clean_paths.append(path)
            frames.append(frame)
    expected = 3 * len(POOLS["heldout"]) * len(__import__("scripts.formal_parallel", fromlist=["METHODS"]).METHODS)
    assert len(clean_paths) == expected == 810
    output = ROOT / "results" / "q3_benign_drift"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "raw_episode_results.csv"
    assert not target.exists(), "Q3 output must be absent at approved switch"
    data = pd.concat(frames, ignore_index=True)
    assert len(data) == expected * 24
    tmp = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    data.to_csv(tmp, index=False, na_rep="NA")
    os.replace(tmp, target)
    save_json(ROOT / "audits" / "q3_execution.json", {
        "status": "passed", "expected_trajectories": expected, "completed_trajectories": expected,
        "stage_rows": len(data), "source": "completed formal Q1 clean trajectories",
        "executor_note": "Q3 is a deterministic derivation with no model workload; two-worker execution starts at Q4",
    })
    save_execution_status(ROOT / "logs" / "execution_status.json", {
        "phase": "Q3", "phase_complete": "Q3", "completed_trajectories": expected,
        "expected_trajectories": expected, "worker_pids": [], "integrity_audit": "PASS",
        "queue_remaining": QUEUE[1:], "heldout_started": True,
    })


def ensure_initial_models(specs, phase):
    unique = list(dict.fromkeys(specs))
    for index, (center, seed, backbone, H) in enumerate(unique, 1):
        initial_model(center, seed, backbone, H)
        if index == 1 or index % 10 == 0 or index == len(unique):
            save_execution_status(ROOT / "logs" / "execution_status.json", {
                "phase": phase, "completed_models": index, "expected_models": len(unique),
                "worker_pids": [], "queue_remaining": QUEUE, "heldout_started": True,
            })


def main():
    lock = ROOT / "logs" / "runner.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    (ROOT / "runner.pid").write_text(str(os.getpid()), encoding="utf-8")
    try:
        freeze = require_executor_switch_freeze()
        update_report("Q3 及后续双 worker 正式队列已启动",
                      f"Execution-only commit `{freeze['git_sha']}`；Q1/Q2 保持 reference 1-worker provenance；"
                      "Q3 及后续采用两个完整 workload worker，科学实现与 frozen protocol 不变。")
        build_q3()
        run_parallel_phase("Q4", q4_jobs(), QUEUE[2:])
        run_parallel_phase("Q5_sensitivity", q5_sensitivity_jobs(), QUEUE[3:])

        for seed, backbone, H in __import__("itertools").product([7311, 7312, 7313], ["MLP", "TCN", "GRU"], [1, 4]):
            pretrain(seed, backbone, H)
        generality = q5_generality_jobs()
        ensure_initial_models([(j["center"], j["seed"], j["backbone"], j["H"]) for j in generality], "Q5_general_initial_models")
        run_parallel_phase("Q5_generality", generality, QUEUE[4:])
        run_parallel_phase("Q5_runtime", q5_runtime_jobs(), QUEUE[5:])
        update_report("Q3–Q5 synthetic heldout 完成", "双 worker 阶段完整性审计全部 PASS；继续 Alibaba 冻结队列。")

        for seed in [7311, 7312, 7313]:
            pretrain(seed, domain="alibaba")
        direct = alibaba_direct_jobs()
        ensure_initial_models([(j["center"], j["seed"], j["backbone"], j["H"]) for j in direct], "Q6_Alibaba_initial_models")
        run_parallel_phase("Q6_Alibaba_direct", direct, QUEUE[6:])

        from scripts.run_calibration_joint_dag_parallel import main as calibrate
        calibrate("alibaba", 2)
        commit_config = json.loads((ROOT / "configs" / "alibaba_frozen_commit_config.yaml").read_text(encoding="utf-8"))
        run_parallel_phase("Q6_Alibaba_diagnostic", alibaba_diagnostic_jobs(commit_config), QUEUE[8:])
        update_report("P13 Alibaba Q6 完成", "Single-policy workloads 使用批准的双 worker；Proposed calibration 使用既有 joint-policy DAG。")

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
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        save_json(ROOT / "logs" / "execution_failure.json", {
            "time": datetime.datetime.now().isoformat(), "error": error,
            "status": "STOPPED_NO_AUTOMATIC_RETRY", "runner": "resume_after_q2_parallel.py",
        })
        raise
    finally:
        lock.unlink(missing_ok=True)
        (ROOT / "runner.pid").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
