"""Programmatic frozen Q2 workload manifest helpers."""
import itertools
import re

from core.protocol import POOLS


Q2_METHODS = [
    "Frozen", "Always-FT", "ER", "EWC", "Huber-FT",
    "CLeaR-Predictor", "ValidationCommit", "Proposed",
]
Q2_SEEDS = [7311, 7312, 7313]


def q2_conditions():
    conditions = [
        (attack, alpha, "both")
        for attack, alpha in itertools.product(
            ["random", "persistent_bias", "burst", "replay"],
            [0.05, 0.1, 0.2],
        )
    ]
    conditions += list(itertools.product(
        ["persistent_bias", "replay"],
        [0.1],
        ["update_only", "verification_only"],
    ))
    return conditions


def q2_workloads():
    return list(itertools.product(
        Q2_SEEDS,
        POOLS["heldout"][:20],
        q2_conditions(),
        Q2_METHODS,
    ))


def q2_key(workload):
    seed, center, (attack, alpha, location), method = workload
    return int(seed), int(center), attack, float(alpha), location, method


_PATTERN = re.compile(
    r"^base_(\d+)_(\d+)_GRU_H1_(" + "|".join(map(re.escape, Q2_METHODS))
    + r")_(random|persistent_bias|burst|replay)_([0-9.]+)_(both|update_only|verification_only)_r0\.csv$"
)


def q2_key_from_filename(name):
    match = _PATTERN.match(name)
    if not match:
        return None
    center, seed, method, attack, alpha, location = match.groups()
    return int(seed), int(center), attack, float(alpha), location, method
