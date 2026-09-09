import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.formal_parallel import (
    alibaba_direct_jobs, partition_jobs, q4_jobs, q5_generality_jobs,
    q5_runtime_jobs, q5_sensitivity_jobs,
)


def test_frozen_denominators_and_unique_filenames():
    expected = {
        "Q4": (q4_jobs(), 360),
        "Q5_sensitivity": (q5_sensitivity_jobs(), 660),
        "Q5_generality": (q5_generality_jobs(), 1800),
        "Q5_runtime": (q5_runtime_jobs(), 400),
        "Q6_Alibaba_direct": (alibaba_direct_jobs(), 2160),
    }
    for _, (jobs, count) in expected.items():
        assert len(jobs) == count
        assert len({job["filename"] for job in jobs}) == count
        assert all(job["stages"] == 24 for job in jobs)


def test_two_worker_partition_keeps_every_lifecycle_whole():
    jobs = q4_jobs()
    bins = partition_jobs(jobs, 2)
    assert len(bins) == 2
    assert sorted(job["filename"] for group in bins for job in group) == sorted(job["filename"] for job in jobs)
    assert not ({job["filename"] for job in bins[0]} & {job["filename"] for job in bins[1]})
