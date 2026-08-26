import json
from datetime import datetime, timezone
from pathlib import Path

PENDING_PATH = Path(__file__).resolve().parents[2] / "pending.json"


def _load() -> list[dict]:
    if not PENDING_PATH.exists():
        return []
    return json.loads(PENDING_PATH.read_text())


def _save(records: list[dict]) -> None:
    PENDING_PATH.write_text(json.dumps(records, indent=2) + "\n")


def mark_pending(request_id: str, volunteer_email: str) -> None:
    records = [r for r in _load() if r["request_id"] != request_id]
    records.append({
        "request_id": request_id,
        "volunteer_email": volunteer_email,
        "notified_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    })
    _save(records)


def mark_resolved(request_id: str, status: str = "resolved") -> None:
    records = _load()
    for r in records:
        if r["request_id"] == request_id:
            r["status"] = status
    _save(records)


def list_overdue(timeout_minutes: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    overdue = []
    for r in _load():
        if r["status"] != "pending":
            continue
        notified_at = datetime.fromisoformat(r["notified_at"])
        age_minutes = (now - notified_at).total_seconds() / 60
        if age_minutes >= timeout_minutes:
            overdue.append(r)
    return overdue
