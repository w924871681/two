"""Worker process for a frozen post-Q2 execution manifest."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from core.engine import run
from core.protocol import ROOT
from core.status import save_execution_status
from scripts.executor_switch_freeze import require_executor_switch_freeze
from scripts.formal_parallel import load_frozen_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--worker", type=int, required=True)
    args = parser.parse_args()
    require_executor_switch_freeze()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    assert manifest["workers"] == 2 and args.worker in [0, 1]
    jobs = manifest["assignments"][str(args.worker)]
    base_cfg = load_frozen_config()
    started = time.time()
    completed = 0
    skipped = 0
    for index, job in enumerate(jobs):
        output = ROOT / "results" / job["output"]
        output.mkdir(parents=True, exist_ok=True)
        path = output / job["filename"]
        if path.exists():
            frame = pd.read_csv(path)
            assert len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)), path
            skipped += 1
        else:
            cfg = {**base_cfg, **job.get("cfg_overrides", {})}
            rows = run(job["center"], job["seed"], job["method"], job["kind"], job["alpha"],
                       job["location"], cfg, backbone=job["backbone"], H=job["H"],
                       run_id=job["filename"][:-4])
            frame = pd.DataFrame(rows)
            assert len(frame) == 24 and frame.stage.tolist() == list(range(1, 25))
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            frame.to_csv(tmp, index=False, na_rep="NA")
            os.replace(tmp, path)
            completed += 1
        status = {
            "phase": manifest["phase"], "worker": args.worker, "pid": os.getpid(),
            "completed_assigned": completed + skipped, "expected_assigned": len(jobs),
            "newly_completed": completed, "skipped_existing": skipped, "last_completed": job["filename"],
            "elapsed_s": time.time() - started, "stages_per_lifecycle": 24,
        }
        save_execution_status(ROOT / "logs" / f"formal_worker{args.worker}.json", status)
        print(f"{manifest['phase']} worker={args.worker} {index + 1}/{len(jobs)} {job['filename']}", flush=True)


if __name__ == "__main__":
    main()
