import json

import numpy as np
import pytest

from core.engine import run
from core.protocol import ROOT, Timeline
from core.v2_engine import V1_GATE, _v2_attack, run_v2


def test_v2_executor_rejects_every_nondevelopment_center():
    structure = {"family": "V1_SP_StaticDual", "structure_id": "test"}
    for center in [10000, 13000, 14000, 20060]:
        with pytest.raises(PermissionError):
            run_v2(center, 7311, structure, stages=1)


def test_v2_attack_is_exact_for_mixed_and_redirects_audit():
    timeline = Timeline(11000)
    update, _ = timeline.maintenance(1)
    attacked, mask, source, actual = _v2_attack(update, 11000, 1, "mixed", 0.1, "both")
    from core.protocol import attack

    reference, ref_mask, ref_source, ref_actual = attack(update, 11000, 1, "mixed", 0.1, "both")
    assert actual == ref_actual
    assert np.array_equal(attacked.x, reference.x)
    assert np.array_equal(attacked.y, reference.y)
    assert np.array_equal(mask, ref_mask)
    assert np.array_equal(source, ref_source)
    assert (ROOT / "scratch_v2/attack_masks").exists()


def test_singlepath_static_dual_is_scientifically_exact_to_v1_executor():
    structure = {"family": "V1_SP_StaticDual", "structure_id": "test_static"}
    v2 = run_v2(11000, 7311, structure, "mixed", 0.1, "both", V1_GATE, stages=2)
    v1 = run(11000, 7311, "SinglePath", "mixed", 0.1, "both", cfg=V1_GATE, stages=2)
    exact = [
        "parent_state_hash",
        "candidate_state_hash",
        "initial_state_hash",
        "commit",
        "deployed_service_mse",
        "deployed_service_mae",
        "delta_srv",
        "harmful_commit",
        "downside",
        "beneficial_candidate",
        "U_rec",
        "attack_mask_hash",
        "update_data_hash",
        "verification_data_hash",
        "service_data_hash",
    ]
    for left, right in zip(v2, v1):
        for key in exact:
            assert left[key] == right[key], (key, left[key], right[key])
        assert left["U_hist_long"] == right["U_hist"]


def test_legacy_candidate_and_static_gate_are_scientifically_exact():
    structure = {"family": "V0_LegacyFull", "structure_id": "test_legacy"}
    v2 = run_v2(11000, 7311, structure, "clean", 0.0, "both", V1_GATE, stages=2)
    v1_cfg = {"B": 5, "beta": 0.1, **V1_GATE}
    v1 = run(11000, 7311, "Proposed", "clean", 0.0, "both", cfg=v1_cfg, stages=2)
    for left, right in zip(v2, v1):
        for key in [
            "parent_state_hash",
            "candidate_state_hash",
            "commit",
            "deployed_service_mse",
            "deployed_service_mae",
            "harmful_commit",
            "downside",
            "attack_mask_hash",
        ]:
            assert left[key] == right[key], (key, left[key], right[key])
        assert left["U_hist_long"] == right["U_hist"]


def test_pool_is_still_sealed_and_unmaterialized():
    seal = json.loads((ROOT / "audits_v2_dev/v2_confirmatory_pool_seal.json").read_text(encoding="utf-8"))
    assert seal["status"] == "PASS"
    assert seal["service_outcomes_accessed"] is False
    assert not any((ROOT / "data" / f"center_{center}.npz").exists() for center in range(14000, 14030))
