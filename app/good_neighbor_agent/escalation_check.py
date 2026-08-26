"""Standalone entrypoint for the scheduled escalation check.

Deliberately does NOT go through the Strands agent/LLM — deciding whether a request
has been pending too long is a mechanical timeout comparison, not a judgment call,
so there's no reason to spend a model call on it. Run via GitHub Actions on a
schedule (see .github/workflows/escalation-check.yml) instead of AWS EventBridge,
since this project avoids a billed AWS account.
"""

import os

from .pending import list_overdue, mark_resolved
from .tools import _send_email

def run() -> list[str]:
    # Read lazily, after load_dotenv() has run — a module-level read here previously
    # always missed .env. See implementation-notes.md.
    timeout_minutes = int(os.environ.get("ESCALATION_TIMEOUT_MINUTES", "10"))
    coordinator_email = os.environ.get("DEMO_INBOX", "coordinator@example.org")

    escalated = []
    for record in list_overdue(timeout_minutes):
        request_id = record["request_id"]
        reason = (
            f"No response from {record['volunteer_email']} within "
            f"{timeout_minutes} minutes (notified at {record['notified_at']})."
        )
        _send_email(
            to=coordinator_email,
            subject=f"[Escalation] request {request_id} needs a human",
            html=f"<p>Request <b>{request_id}</b> timed out.</p><p>{reason}</p>",
        )
        mark_resolved(request_id, "escalated")
        escalated.append(request_id)
    return escalated


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    result = run()
    print(f"Escalated {len(result)} request(s): {result}")
