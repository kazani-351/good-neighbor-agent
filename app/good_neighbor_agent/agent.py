import os

from strands import Agent
from strands.models.openai import OpenAIModel

from .tools import escalate, find_volunteer, log_outcome, notify_volunteer

# thegrid.ai is an OpenAI-compatible inference marketplace — see
# https://thegrid.ai/docs/integrations-and-best-practices/integrations/general-agent-skill
# "agent-prime" is their general-purpose tool-calling instrument.
THEGRID_BASE_URL = "https://api.thegrid.ai/v1"
THEGRID_MODEL_ID = "agent-prime"

SYSTEM_PROMPT = """You coordinate accessibility requests for a small volunteer network that
helps blind and low-vision neighbors with tasks like reading labels, forms, or navigation.

For each request:
1. If you can answer directly and confidently from what's given (including any photo), just
   answer — don't involve a volunteer for something you can already do well.
2. If you're not confident, or the task needs a human who can act in the physical world,
   call find_volunteer with the relevant skill, then notify_volunteer.
3. If find_volunteer returns nothing available, or the situation sounds safety-critical
   (e.g. medication, an unsafe location), call escalate instead of leaving it unresolved.
4. Always call log_outcome at the end with what actually happened.

Give each request a short request_id you make up (e.g. "req-<short random string>") and use
it consistently across notify_volunteer, escalate, and log_outcome.
"""


def build_agent() -> Agent:
    model = OpenAIModel(
        client_args={
            "api_key": os.environ["THEGRID_API_KEY"],
            "base_url": THEGRID_BASE_URL,
        },
        model_id=THEGRID_MODEL_ID,
    )
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[find_volunteer, notify_volunteer, escalate, log_outcome],
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = build_agent()
    agent("A neighbor says: 'Can someone tell me what this pill bottle label says? "
          "I don't have a photo, just the words: Metformin 500mg, take twice daily.'")
