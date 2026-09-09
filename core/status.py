"""Best-effort execution telemetry publishing.

Scientific results must never depend on whether a status snapshot can be
published.  In particular, Windows readers can briefly prevent os.replace.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import time


DEFAULT_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8)


def _is_transient_replace_error(exc: PermissionError) -> bool:
    return getattr(exc, "winerror", None) in (5, 32) or getattr(exc, "errno", None) == 13


def save_execution_status(path, obj, *, retry_delays=DEFAULT_RETRY_DELAYS, warning_path=None):
    """Publish a JSON status snapshot without making telemetry scientific state.

    The temporary file is fully written, flushed, fsynced, and closed before
    replacement.  A transient Windows sharing violation is retried for a
    bounded period.  Persistent telemetry failure is logged and returns False;
    it does not invalidate or roll back an already published trajectory CSV.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    warning_path = Path(warning_path) if warning_path else path.parent / "execution_status_warnings.log"
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(obj, indent=2, allow_nan=False)
    with tmp.open("w", encoding="utf-8", newline="") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())

    last_error = None
    for attempt in range(len(retry_delays) + 1):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError as exc:
            if not _is_transient_replace_error(exc):
                raise
            last_error = exc
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])

    warning = {
        "time": datetime.datetime.now().isoformat(),
        "event": "execution_status_publish_failed",
        "path": str(path),
        "attempts": len(retry_delays) + 1,
        "error": repr(last_error),
        "scientific_trajectory_preserved": True,
    }
    try:
        with warning_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(warning, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        pass
    try:
        tmp.unlink(missing_ok=True)
    except OSError:
        pass
    return False
