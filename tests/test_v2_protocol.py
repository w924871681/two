import json

from core.protocol import ROOT
from scripts.v2_analyze import EPSILON, RHO
from scripts.v2_runner import CALIBRATION_CENTERS, DEVELOPMENT_CENTERS, make_jobs, structural_grid


def test_v2_structural_grid_is_exactly_preregistered():
    grid = structural_grid()
    assert len(grid) == 20
    assert sum(x["family"] == "V3_SP_AdaptiveDual" for x in grid) == 8
    assert sum(x["family"] == "V4_SP_AdaptiveDual_NoRealign" for x in grid) == 8
    assert {x.get("h_short") for x in grid if x["family"].startswith("V3_")} == {6, 12}
    assert {x.get("support_min_fraction") for x in grid if x["family"].startswith("V3_")} == {"4/6", "5/6"}
    assert {x.get("r_persist") for x in grid if x["family"].startswith("V3_")} == {2, 3}
    assert sum(bool(x.get("diagnostic_only")) for x in grid) == 1


def test_v2_fixed_risk_constraints_match_v1():
    protocol = json.loads((ROOT / "configs/calibration_protocol.yaml").read_text(encoding="utf-8"))
    assert RHO == protocol["rho"] == 0.05
    assert EPSILON == protocol["epsilon"]


def test_development_manifest_denominator_and_pools(tmp_path):
    jobs = make_jobs("development", tmp_path)
    assert len(jobs) == 4800
    assert {j["center"] for j in jobs} == set(DEVELOPMENT_CENTERS)
    assert not ({j["center"] for j in jobs} & set(range(13000, 14030)))


def test_confirmatory_pool_remains_unmaterialized():
    assert all(not (ROOT / "data" / f"center_{center}.npz").exists() for center in range(14000, 14030))
    seal = json.loads((ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json").read_text(encoding="utf-8"))
    assert seal["status"] == "SEALED_NOT_MATERIALIZED"
