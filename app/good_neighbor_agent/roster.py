import json
import os
from pathlib import Path

ROSTER_PATH = Path(__file__).resolve().parents[2] / "volunteers.json"


def load_volunteers() -> list[dict]:
    return json.loads(ROSTER_PATH.read_text())


def find_available(skill: str) -> dict | None:
    for volunteer in load_volunteers():
        if volunteer["available"] and skill in volunteer["skills"]:
            # DEMO_INBOX overrides the committed placeholder email at runtime so local
            # testing/demo actually delivers somewhere real, without putting a real
            # address in this file, which ships in the public submission repo.
            demo_inbox = os.environ.get("DEMO_INBOX")
            if demo_inbox:
                volunteer = {**volunteer, "email": demo_inbox}
            return volunteer
    return None
