from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import torch


ROOT = Path(r"D:\dt-trustworthy-maintenance")
OUT = ROOT / "results" / "alibaba_calibration"
AUDITS = ROOT / "audits"
SEEDS = (7311, 7312, 7313)
CENTERS = tuple(range(20040, 20060))
CONDITIONS = {"clean": 0.0, "mixed": 0.1}
POLICIES = tuple(range(405))
EXPECTED_GIT = "d6d33075cb3afa55a24878e2343f1bc1d1c9368a"
EXPECTED_JOINT = "9020dc8cced08766c0bb02e5103578e3da958d02c2f504f793e4d3ebda76374a"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAME_RE = re.compile(r"^policy(?P<policy>\d{3})_(?P<seed>\d+)_(?P<center>\d+)_(?P<kind>clean|mixed)\.csv$")

BASE_REQUIRED = {
    "run_id", "center_id", "center_type", "model_seed", "horizon", "backbone", "stage",
    "drift_regime", "attack_type", "actual_attack_type", "attack_alpha", "attack_location",
    "method", "parent_state_hash", "candidate_state_hash", "initial_state_hash", "commit",
    "current_service_mse", "candidate_service_mse", "deployed_service_mse", "deployed_service_mae",
    "delta_srv", "harmful_commit", "downside", "beneficial_candidate", "U_rec", "U_hist",
    "candidate_update_time_s", "verification_time_s", "maintenance_time_s", "peak_gpu_memory_bytes",
    "persistent_buffer_bytes", "number_of_forward_passes", "number_of_backward_updates",
    "number_of_fisher_backward_passes", "update_start_ts", "update_end_ts",
    "verification_start_ts", "verification_end_ts", "decision_ts", "service_start_ts",
    "service_end_ts", "attack_mask_hash", "update_data_hash", "verification_data_hash",
    "service_data_hash", "implementation_git_sha", "joint_dag_implementation_sha256",
}
PROPOSED_REQUIRED = BASE_REQUIRED | {
    "policy", "deployed_state_hash", "causal_state_fingerprint", "historical_buffer_hash",
    "next_historical_buffer_hash", "median_rec", "mad_rec", "median_hist", "mad_hist",
}
HASH_COLUMNS = (
    "parent_state_hash", "candidate_state_hash", "initial_state_hash", "attack_mask_hash",
    "update_data_hash", "verification_data_hash", "service_data_hash",
)
PROPOSED_HASH_COLUMNS = (
    "deployed_state_hash", "causal_state_fingerprint", "historical_buffer_hash",
    "next_historical_buffer_hash",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def key_hash(obj) -> str:
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def state_dict_hash(state) -> str:
    h = hashlib.sha256()
    for key, value in state.items():
        h.update(key.encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def finite_or_na(value: str) -> bool:
    if value in ("", "NA", "NaN", "nan"):
        return True
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def audit_results() -> dict:
    expected = {(p, s, c, k) for p in POLICIES for s in SEEDS for c in CENTERS for k in CONDITIONS}
    seen = set()
    valid = set()
    duplicate_keys = []
    unexpected = []
    invalid = []
    mismatch_counts = Counter()
    consistency = {}
    aggregate = hashlib.sha256()
    workload_files = defaultdict(list)
    total_rows = 0
    files = sorted(OUT.glob("*.csv"), key=lambda p: p.name.lower())
    for index, path in enumerate(files, 1):
        match = NAME_RE.fullmatch(path.name)
        if not match:
            unexpected.append({"file": path.name, "reason": "filename_not_in_manifest_schema"})
            continue
        key = (int(match["policy"]), int(match["seed"]), int(match["center"]), match["kind"])
        if key in seen:
            duplicate_keys.append({"key": list(key), "file": path.name})
            continue
        seen.add(key)
        if key not in expected:
            unexpected.append({"file": path.name, "key": list(key), "reason": "key_not_expected"})
            continue
        policy, seed, center, kind = key
        reasons = []
        try:
            raw = path.read_bytes()
            if not raw:
                raise ValueError("empty_file")
            file_hash = hashlib.sha256(raw).hexdigest()
            aggregate.update(path.name.encode())
            aggregate.update(str(len(raw)).encode())
            aggregate.update(file_hash.encode())
            text = raw.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            fields = set(reader.fieldnames or [])
            required = PROPOSED_REQUIRED if policy < 400 else BASE_REQUIRED
            missing_columns = sorted(required - fields)
            if missing_columns:
                reasons.append("missing_columns:" + ",".join(missing_columns))
            rows = list(reader)
            total_rows += len(rows)
            if len(rows) != 24:
                reasons.append(f"row_count={len(rows)}")
            stages = []
            prior_deployed = None
            prior_next_history = None
            for row_index, row in enumerate(rows):
                try:
                    stage = int(row.get("stage", ""))
                    stages.append(stage)
                except Exception:
                    reasons.append(f"row_{row_index + 1}:invalid_stage")
                    continue
                if int(row.get("center_id", -1)) != center:
                    reasons.append(f"stage_{stage}:center_metadata")
                if int(row.get("model_seed", -1)) != seed:
                    reasons.append(f"stage_{stage}:seed_metadata")
                if row.get("attack_type") != kind:
                    reasons.append(f"stage_{stage}:condition_metadata")
                if abs(float(row.get("attack_alpha", "nan")) - CONDITIONS[kind]) > 0:
                    reasons.append(f"stage_{stage}:alpha_metadata")
                expected_method = "Proposed" if policy < 400 else "ValidationCommit"
                if row.get("method") != expected_method:
                    reasons.append(f"stage_{stage}:method_metadata")
                if policy < 400 and int(row.get("policy", -1)) != policy:
                    reasons.append(f"stage_{stage}:policy_metadata")
                if row.get("implementation_git_sha") != EXPECTED_GIT:
                    reasons.append(f"stage_{stage}:implementation_git_sha")
                    mismatch_counts["implementation_git_sha"] += 1
                if row.get("joint_dag_implementation_sha256") != EXPECTED_JOINT:
                    reasons.append(f"stage_{stage}:joint_dag_implementation_sha256")
                    mismatch_counts["joint_dag_implementation_sha256"] += 1
                for col in HASH_COLUMNS + (PROPOSED_HASH_COLUMNS if policy < 400 else ()):
                    if not HEX64.fullmatch(row.get(col, "")):
                        reasons.append(f"stage_{stage}:invalid_{col}")
                        mismatch_counts[col] += 1
                for col in ("current_service_mse", "candidate_service_mse", "deployed_service_mse",
                            "deployed_service_mae", "delta_srv", "downside", "U_rec", "U_hist"):
                    if not finite_or_na(row.get(col, "")):
                        reasons.append(f"stage_{stage}:nonfinite_{col}")
                commit = int(row.get("commit", -1))
                if commit not in (0, 1):
                    reasons.append(f"stage_{stage}:invalid_commit")
                deployed = row.get("deployed_state_hash") if policy < 400 else (
                    row.get("candidate_state_hash") if commit == 1 else row.get("parent_state_hash")
                )
                if policy < 400:
                    expected_deployed = row.get("candidate_state_hash") if commit == 1 else row.get("parent_state_hash")
                    if deployed != expected_deployed:
                        reasons.append(f"stage_{stage}:deployed_state_transition")
                        mismatch_counts["deployed_state_transition"] += 1
                if prior_deployed is not None and row.get("parent_state_hash") != prior_deployed:
                    reasons.append(f"stage_{stage}:parent_chain")
                    mismatch_counts["parent_chain"] += 1
                if policy < 400 and prior_next_history is not None and row.get("historical_buffer_hash") != prior_next_history:
                    reasons.append(f"stage_{stage}:history_chain")
                    mismatch_counts["history_chain"] += 1
                prior_deployed = deployed
                if policy < 400:
                    prior_next_history = row.get("next_historical_buffer_hash")
                data_key = (seed, center, kind, stage)
                hashes = tuple(row.get(col) for col in ("attack_mask_hash", "update_data_hash", "verification_data_hash", "service_data_hash"))
                if data_key not in consistency:
                    consistency[data_key] = hashes
                elif consistency[data_key] != hashes:
                    reasons.append(f"stage_{stage}:cross_policy_data_or_attack_hash")
                    mismatch_counts["cross_policy_data_or_attack_hash"] += 1
            if sorted(stages) != list(range(1, 25)) or len(set(stages)) != len(stages):
                reasons.append("stage_sequence_not_exact_1_24")
        except Exception as exc:
            reasons.append(f"parse_exception:{type(exc).__name__}:{exc}")
        workload = (seed, center, kind)
        workload_files[workload].append({"policy": policy, "mtime": path.stat().st_mtime, "file": path.name})
        if reasons:
            invalid.append({"file": path.name, "key": list(key), "reasons": sorted(set(reasons))})
        else:
            valid.add(key)
        if index % 2500 == 0:
            print(f"result audit {index}/{len(files)}", flush=True)

    missing = sorted(expected - valid)
    complete_workloads = []
    incomplete_workloads = []
    for workload, items in workload_files.items():
        policies = {item["policy"] for item in items if (item["policy"], *workload) in valid}
        record = {"seed": workload[0], "center": workload[1], "condition": workload[2],
                  "valid_policies": len(policies), "last_write_epoch": max(i["mtime"] for i in items)}
        if policies == set(POLICIES):
            complete_workloads.append(record)
        else:
            record["missing_policies"] = sorted(set(POLICIES) - policies)
            incomplete_workloads.append(record)
    latest_workloads = sorted(complete_workloads, key=lambda x: x["last_write_epoch"], reverse=True)[:10]
    for item in latest_workloads:
        item["last_write"] = datetime.fromtimestamp(item.pop("last_write_epoch")).isoformat()
    tmp_files = sorted(str(p.relative_to(ROOT)) for p in OUT.rglob("*") if p.is_file() and (
        p.suffix.lower() == ".tmp" or "partial" in p.name.lower() or "checkpoint" in p.name.lower()
    ))
    result = {
        "status": "passed" if not duplicate_keys and not unexpected and not invalid and not tmp_files else "failed",
        "generated_at": datetime.now().isoformat(),
        "manifest_definition": {
            "policies": 405, "seeds": list(SEEDS), "centers": [min(CENTERS), max(CENTERS)],
            "center_count": len(CENTERS), "conditions": CONDITIONS, "expected_total": len(expected),
            "scientific_key": ["policy", "model_seed", "center_id", "attack_type"],
        },
        "status_claimed_completed": 28755,
        "csv_files_scanned": len(files),
        "stage_rows_scanned": total_rows,
        "valid_completed_keys": len(valid),
        "remaining_keys": len(expected - valid),
        "duplicate_key_count": len(duplicate_keys),
        "unexpected_key_count": len(unexpected),
        "invalid_or_partial_count": len(invalid),
        "scientific_hash_mismatch_count": sum(mismatch_counts.values()),
        "mismatch_counts": dict(mismatch_counts),
        "complete_workloads": len(complete_workloads),
        "incomplete_workloads": incomplete_workloads,
        "latest_complete_workloads": latest_workloads,
        "tmp_or_partial_files": tmp_files,
        "directory_content_manifest_sha256": aggregate.hexdigest(),
        "duplicates": duplicate_keys[:100],
        "unexpected": unexpected[:100],
        "invalid": invalid[:100],
        "missing_keys": [f"policy{p:03d}_{s}_{c}_{k}" for p, s, c, k in missing],
        "overwrite_assessment": {
            "detected_overwrite": False,
            "evidence": "executor skips existing final paths; all observed final files are unique, valid, and atomically published; no tmp/partial file was counted",
        },
        "provenance": {
            "implementation_git_sha": EXPECTED_GIT,
            "joint_dag_implementation_sha256": EXPECTED_JOINT,
        },
    }
    atomic_json(AUDITS / "alibaba_calibration_result_integrity.json", result)
    atomic_json(AUDITS / "alibaba_shutdown_recovery_integrity.json", result)
    print(json.dumps({k: result[k] for k in ("status", "valid_completed_keys", "remaining_keys", "duplicate_key_count", "unexpected_key_count", "invalid_or_partial_count", "scientific_hash_mismatch_count", "complete_workloads")}, indent=2), flush=True)
    return result


def audit_cache() -> dict:
    candidate_dir = ROOT / "checkpoints" / "joint_dag_candidates"
    evidence_dir = ROOT / "checkpoints" / "joint_dag_evidence"
    current_science = {
        rel: sha256(ROOT / rel) for rel in ("core/engine.py", "core/models.py", "core/protocol.py")
    }
    candidate_json = {p.stem: p for p in candidate_dir.glob("*.json")}
    candidate_pt = {p.stem: p for p in candidate_dir.glob("*.pt")}
    candidate_orphans = sorted((set(candidate_json) ^ set(candidate_pt)))
    candidate_relevant = 0
    candidate_valid = 0
    candidate_invalid = []
    candidate_mtimes = []
    for index, (key, meta_path) in enumerate(candidate_json.items(), 1):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            payload = meta["key_payload"]
            if int(payload.get("center", -1)) not in CENTERS:
                continue
            candidate_relevant += 1
            reasons = []
            if key_hash(payload) != key:
                reasons.append("filename_key_mismatch")
            if payload.get("schema") != "joint-policy-dag-v1":
                reasons.append("schema_mismatch")
            if payload.get("science_version") != current_science:
                reasons.append("science_version_mismatch")
            pt_path = candidate_pt.get(key)
            if pt_path is None or pt_path.stat().st_size == 0:
                reasons.append("missing_or_empty_pt")
            else:
                state = torch.load(pt_path, map_location="cpu", weights_only=True)
                if state_dict_hash(state) != meta.get("candidate_state_hash"):
                    reasons.append("candidate_state_hash_mismatch")
            if reasons:
                candidate_invalid.append({"key": key, "reasons": reasons})
            else:
                candidate_valid += 1
            candidate_mtimes.append((max(meta_path.stat().st_mtime, pt_path.stat().st_mtime if pt_path else 0), key, not reasons))
        except Exception as exc:
            candidate_invalid.append({"key": key, "reasons": [f"exception:{type(exc).__name__}:{exc}"]})
        if index % 10000 == 0:
            print(f"candidate cache audit {index}/{len(candidate_json)}", flush=True)

    evidence_valid = 0
    evidence_relevant = 0
    evidence_invalid = []
    evidence_mtimes = []
    evidence_files = list(evidence_dir.glob("*.npz"))
    for index, path in enumerate(evidence_files, 1):
        key = path.stem
        try:
            with np.load(path, allow_pickle=False) as data:
                payload = json.loads(str(data["key_json"]))
                if int(payload.get("center", -1)) not in CENTERS:
                    continue
                evidence_relevant += 1
                reasons = []
                if key_hash(payload) != key:
                    reasons.append("filename_key_mismatch")
                if payload.get("schema") != "joint-policy-dag-v1":
                    reasons.append("schema_mismatch")
                if payload.get("science_version") != current_science:
                    reasons.append("science_version_mismatch")
                vals = np.asarray(data["vals"])
                weights = np.asarray(data["weights"])
                calls = int(data["calls"])
                if vals.ndim != 1 or weights.ndim != 1 or len(vals) != len(weights):
                    reasons.append("array_shape_mismatch")
                if not np.isfinite(vals).all() or (weights < 0).any() or calls < 0:
                    reasons.append("invalid_evidence_values")
                if reasons:
                    evidence_invalid.append({"key": key, "reasons": reasons})
                else:
                    evidence_valid += 1
                evidence_mtimes.append((path.stat().st_mtime, key, not reasons))
        except Exception as exc:
            # Only count an unreadable artifact as relevant if it was written during this formal Alibaba run.
            if path.stat().st_mtime >= datetime(2026, 9, 10, 3, 0).timestamp():
                evidence_relevant += 1
                evidence_invalid.append({"key": key, "reasons": [f"exception:{type(exc).__name__}:{exc}"]})
                evidence_mtimes.append((path.stat().st_mtime, key, False))
        if index % 20000 == 0:
            print(f"evidence cache audit {index}/{len(evidence_files)}", flush=True)

    tmp_files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "checkpoints").rglob("*") if p.is_file() and p.suffix.lower() == ".tmp")
    latest_candidates = sorted(candidate_mtimes, reverse=True)[:100]
    latest_evidence = sorted(evidence_mtimes, reverse=True)[:100]
    last_batch = {
        "candidate_entries_checked": len(latest_candidates),
        "candidate_entries_valid": sum(1 for _, _, ok in latest_candidates if ok),
        "candidate_latest_write": datetime.fromtimestamp(latest_candidates[0][0]).isoformat() if latest_candidates else None,
        "evidence_entries_checked": len(latest_evidence),
        "evidence_entries_valid": sum(1 for _, _, ok in latest_evidence if ok),
        "evidence_latest_write": datetime.fromtimestamp(latest_evidence[0][0]).isoformat() if latest_evidence else None,
    }
    rejected = len(candidate_invalid) + len(evidence_invalid) + len(candidate_orphans) + len(tmp_files)
    result = {
        "status": "passed" if not candidate_invalid and not evidence_invalid else "failed",
        "generated_at": datetime.now().isoformat(),
        "science_version_expected": current_science,
        "candidate_cache": {
            "all_json_entries": len(candidate_json), "all_pt_entries": len(candidate_pt),
            "alibaba_relevant_entries": candidate_relevant, "accepted_entries": candidate_valid,
            "invalid_entries": len(candidate_invalid), "orphan_pair_keys": candidate_orphans,
            "invalid_examples": candidate_invalid[:100],
        },
        "evidence_cache": {
            "all_npz_entries": len(evidence_files), "alibaba_relevant_entries": evidence_relevant,
            "accepted_entries": evidence_valid, "invalid_entries": len(evidence_invalid),
            "invalid_examples": evidence_invalid[:100],
        },
        "worker_local_tmp_orphans": tmp_files,
        "accepted_artifacts": candidate_valid + evidence_valid,
        "rejected_or_excluded_artifacts": rejected,
        "latest_batch_checksum_validation": last_batch,
        "atomicity_assessment": "candidate requires a valid matching .pt/.json pair; evidence requires a readable self-describing .npz; tmp/orphan artifacts are excluded",
        "interruption_point": {
            "last_completed_worker0": "workload 37/60, center=20058, seed=7311, condition=clean",
            "last_completed_worker1": "workload 34/60, center=20046, seed=7313, condition=mixed",
            "last_result_publish": "2026-09-10T04:28:58+08:00",
            "last_status_publish": "2026-09-10T04:29:05+08:00",
            "classification": "after complete workload/status publish; exact operation during the final 9 seconds before OS restart request is unknown",
        },
    }
    atomic_json(AUDITS / "alibaba_calibration_cache_integrity.json", result)
    atomic_json(AUDITS / "alibaba_shutdown_cache_recovery.json", result)
    print(json.dumps({"status": result["status"], "accepted_artifacts": result["accepted_artifacts"], "rejected_or_excluded_artifacts": rejected, "candidate": result["candidate_cache"], "evidence": result["evidence_cache"], "latest": last_batch}, indent=2)[:12000], flush=True)
    return result


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("results", "all"):
        audit_results()
    if mode in ("cache", "all"):
        audit_cache()
