"""Validate P7 freeze plus the separately approved execution-only recovery layer."""
import hashlib
import json
from pathlib import Path
import subprocess

from core.protocol import ROOT


APPROVED_EXECUTION_ONLY = [
    "scripts/run_heldout.py",
    "core/status.py",
    "scripts/q2_manifest.py",
    "scripts/audit_q2_integrity.py",
    "scripts/resume_q2_after_crash.py",
]


def _hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_q2_recovery_freeze():
    p7 = json.loads((ROOT / "audits/final_freeze.json").read_text())
    recovery = json.loads((ROOT / "audits/q2_recovery_implementation.json").read_text())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert recovery["status"] == "approved_for_q2_recovery"
    assert recovery["recovery_git_sha"] == head
    for relative, expected in p7["files"].items():
        if relative == "scripts/run_heldout.py":
            continue
        assert _hash_file(ROOT / relative) == expected, "P7 frozen file changed: " + relative
    for relative in APPROVED_EXECUTION_ONLY:
        expected = recovery["execution_only_sha256"].get(relative)
        assert expected and _hash_file(ROOT / relative) == expected, "recovery execution file changed: " + relative
    return {"p7": p7, "recovery": recovery}
