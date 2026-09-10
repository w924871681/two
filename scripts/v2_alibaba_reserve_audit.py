"""Metadata-only feasibility audit for a fresh Alibaba V2 reserve."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.prepare_alibaba import ARCHIVE, EXPECTED, chunks


ROOT = Path(__file__).resolve().parents[1]
TARGET = 40


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    archive_hash = hash_file(ARCHIVE)
    if archive_hash != EXPECTED:
        raise RuntimeError("Alibaba archive checksum mismatch")
    prior = json.loads((ROOT / "alibaba_pool_manifest.json").read_text(encoding="utf-8"))
    used_hashes = set(prior["excluded_hashes"])
    used_hashes.update(item["machine_id_hash"] for item in prior["machines"])

    counts: Counter[str] = Counter()
    total_rows = 0
    for frame in chunks():
        valid = frame[frame[2].between(0, 100) & frame[1].notna()]
        counts.update({str(k): int(v) for k, v in valid[0].value_counts().items()})
        total_rows += len(frame)
        print(f"Alibaba V2 eligibility pass rows={total_rows}", flush=True)
    raw_eligible = [mid for mid, count in counts.items() if count >= 16760]
    unused = [mid for mid in raw_eligible if hashlib.sha256(mid.encode()).hexdigest() not in used_hashes]
    ordered = sorted(unused, key=lambda mid: hashlib.sha256(("7311:" + mid).encode()).hexdigest())

    # Verify exact V1 eligibility after timestamp deduplication for a bounded prefix.
    prefix = set(ordered[: max(200, TARGET * 4)])
    timestamps: dict[str, set[int]] = defaultdict(set)
    total_rows = 0
    for frame in chunks():
        part = frame[frame[0].astype(str).isin(prefix)]
        part = part[part[2].between(0, 100) & part[1].notna()]
        for mid, group in part.groupby(0):
            timestamps[str(mid)].update(int(x) for x in group[1].to_numpy())
        total_rows += len(frame)
        print(f"Alibaba V2 uniqueness pass rows={total_rows}", flush=True)
    exact_eligible = [mid for mid in ordered if len(timestamps.get(mid, set())) >= 16760]
    selected = exact_eligible[:TARGET]

    if len(selected) >= TARGET:
        status = "PASS"
        conclusion = "FRESH_EXTERNAL_CONFIRMATORY_POOL_AVAILABLE"
        reserve = [
            {
                "center_id": 20100 + i,
                "machine_id_hash": hashlib.sha256(mid.encode()).hexdigest(),
                "ordering_key_sha256": hashlib.sha256(("7311:" + mid).encode()).hexdigest(),
                "unique_valid_timestamps": len(timestamps[mid]),
            }
            for i, mid in enumerate(selected)
        ]
    else:
        status = "PASS"
        conclusion = "NO_FRESH_EXTERNAL_CONFIRMATORY_POOL"
        reserve = []

    audit = {
        "schema": "ravm-dt-v2-alibaba-reserve-feasibility-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "conclusion": conclusion,
        "audit_scope": "metadata and eligibility only; no V2 model execution and no outcome-based selection",
        "archive_sha256": archive_hash,
        "v1_manifest_sha256": hash_file(ROOT / "alibaba_pool_manifest.json"),
        "eligibility_rule": "CPU usage in [0,100], non-null timestamp, at least 16760 unique valid timestamps after deduplication",
        "ordering_rule": "ascending SHA256('7311:' + machine_id), identical deterministic ordering family to V1",
        "historically_used_or_excluded_machine_hashes": len(used_hashes),
        "raw_eligible_machine_count": len(raw_eligible),
        "unused_raw_eligible_machine_count": len(unused),
        "exactly_verified_prefix_count": len(prefix),
        "exact_eligible_in_verified_prefix": len(exact_eligible),
        "requested_reserve_count": TARGET,
        "reserve": reserve,
        "raw_machine_ids_persisted": False,
        "model_executed": False,
        "performance_metrics_accessed": False,
    }
    atomic_json(ROOT / "audits_v2_dev/alibaba_v2_reserve_feasibility.json", audit)
    print(json.dumps({k: audit[k] for k in ["status", "conclusion", "raw_eligible_machine_count", "unused_raw_eligible_machine_count", "exact_eligible_in_verified_prefix", "requested_reserve_count"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
