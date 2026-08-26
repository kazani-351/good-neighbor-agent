import json
import os
from datetime import datetime, timezone
from pathlib import Path

import resend
from resend.exceptions import ResendError
from strands import tool

from .pending import mark_pending, mark_resolved
from .roster import find_available

LOG_PATH = Path(__file__).resolve().parents[2] / "outcomes.log"

# No custom domain is verified for this project, so sends go from Resend's shared
# sandbox address. Until a domain is verified, Resend only delivers to the account
# owner's own registered email — fine for a hackathon demo, not for a real volunteer
# network. See implementation-notes.md.
NOTIFY_FROM = "Good Neighbor Agent <onboarding@resend.dev>"

def _coordinator_email() -> str:
    # Reuses DEMO_INBOX as the demo "coordinator" — no separate role infrastructure
    # exists yet, and this project deliberately doesn't ship a real address in the
    # public repo. Read lazily (not at module level) so it sees .env after load_dotenv()
    # runs — a module-level read here previously always missed it. See implementation-notes.md.
    return os.environ.get("DEMO_INBOX", "coordinator@example.org")


def _send_email(to: str, subject: str, html: str) -> tuple[bool, str]:
    """Shared send path for both notify_volunteer and escalate. Plain function
    (not @tool) so it's callable directly from the standalone escalation checker
    without going through an agent/LLM call for what's a mechanical send."""
    resend.api_key = os.environ["RESEND_API_KEY"]
    try:
        resend.Emails.send({"from": NOTIFY_FROM, "to": [to], "subject": subject, "html": html})
    except ResendError as error:
        print(f"[_send_email] send failed for {to}: {error}")
        return False, str(error)
    return True, ""


@tool
def find_volunteer(skill: str) -> dict:
    """
    Find an available volunteer who has the given skill.

    Args:
        skill (str): The skill needed, e.g. "reading", "labels", "navigation", "errands".

    Returns:
        dict: The matched volunteer's id, name, and email, or an empty dict if none found.
    """
    volunteer = find_available(skill)
    return volunteer or {}


@tool
def notify_volunteer(request_id: str, volunteer_email: str, request_summary: str) -> str:
    """
    Notify a volunteer about a request they've been matched to.

    Args:
        request_id (str): The id of the request, used to track it until resolved.
        volunteer_email (str): The volunteer's email address.
        request_summary (str): A short summary of what's needed.

    Returns:
        str: Confirmation message, or an error message if the send failed.
    """
    ok, error = _send_email(
        to=volunteer_email,
        subject="A neighbor needs a hand",
        html=f"<p>{request_summary}</p><p>Reply to this email if you can help.</p>",
    )
    if not ok:
        return f"Failed to notify {volunteer_email}: {error}"
    mark_pending(request_id, volunteer_email)
    return f"Notified {volunteer_email}"


@tool
def escalate(request_id: str, reason: str) -> str:
    """
    Escalate a request to a human coordinator because it needs a real decision —
    no volunteer responded in time, or the request looks safety-critical.

    Args:
        request_id (str): The id of the request being escalated.
        reason (str): Why this needs human attention.

    Returns:
        str: Confirmation message, or an error message if the send failed.
    """
    ok, error = _send_email(
        to=_coordinator_email(),
        subject=f"[Escalation] request {request_id} needs a human",
        html=f"<p>Request <b>{request_id}</b> needs attention.</p><p>Reason: {reason}</p>",
    )
    mark_resolved(request_id, "escalated")
    if not ok:
        return f"Escalation email failed for {request_id}: {error}"
    return f"Escalated {request_id}"


@tool
def log_outcome(request_id: str, outcome: str) -> None:
    """
    Record how a request was resolved.

    Args:
        request_id (str): The id of the request.
        outcome (str): What happened — e.g. "answered directly", "volunteer: v1", "escalated".
    """
    entry = {
        "request_id": request_id,
        "outcome": outcome,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
