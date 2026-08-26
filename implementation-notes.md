# Implementation Notes

## Deviations

- **2026-08-25 — httpcore2 async-generator cleanup warning, not fixed, not a bug in our code.**
  Multi-tool test runs sometimes print a `RuntimeError: generator didn't stop after athrow()`
  traceback from `httpcore2`'s async cleanup, after the correct response is already produced.
  Root cause: `agent()` wraps each call in its own `asyncio.run()`, which force-closes any
  still-open async generators at teardown — a known unresolved upstream Python asyncio issue
  (`python-trio/trio#265`, `#2081`), not specific to this project's code. Confirmed both test
  runs still wrote correct output and correct `outcomes.log` entries despite the warning.
  Expected to not reproduce under AgentCore Runtime or any persistent-event-loop deployment,
  since the trigger is tearing down the loop after every disposable one-shot script invocation.
  Not fixing — upstream, cosmetic, no observed impact on correctness. Re-check before the demo
  video if it appears there too.

- **2026-08-25 — SES swapped for Resend before it was ever wired.** SPEC.md originally listed
  Amazon SES for volunteer notification, carried over from the initial Bedrock-based
  architecture sketch. Caught before implementation: SES requires the same billed AWS account
  this project deliberately avoids by using thegrid.ai instead of Bedrock. Resend's free tier
  (100/day, 3,000/month) covers hackathon-demo volume with no AWS dependency. No code was
  written against SES, so this was a spec correction, not a rewrite.

- **2026-08-26 — Resend sandbox restriction: without a verified domain, can only send to
  the account owner's own email.** Confirmed by testing: sending to the seed roster's fake
  `@example.org` addresses (or even an unrelated real address) fails with "You can only send
  testing emails to your own email address." `notify_volunteer` works correctly when the
  recipient is the Resend account's own registered address (`kazani@disroot.org`).
  **Resolved 2026-08-26**: not by editing `volunteers.json` (would put a real personal email
  in the public submission repo — caught before it shipped). Instead, `roster.py` overrides
  the matched volunteer's email with a `DEMO_INBOX` env var at runtime if set, gitignored,
  never committed. Committed seed data stays generic; local demo/test runs deliver for real.

- **2026-08-26 — module-level env var read missed .env, caught by testing not inspection.**
  `COORDINATOR_EMAIL`/`ESCALATION_TIMEOUT_MINUTES` were assigned at module import time in
  `tools.py` and `escalation_check.py`, which runs before `load_dotenv()` executes in the
  `__main__` block — so they always saw the pre-dotenv environment and silently fell back to
  the placeholder address. `roster.py`'s equivalent `DEMO_INBOX` read worked correctly because
  it's inside a function body (evaluated lazily, after dotenv has loaded), not at module level.
  Found by actually testing escalation delivery end-to-end (real send failed against the
  placeholder despite DEMO_INBOX being set) rather than by code review — worth remembering as
  a general pattern: any `os.environ.get(...)` used as a module-level constant in this codebase
  is a bug waiting to happen if it depends on `load_dotenv()`. Fixed by moving both reads
  inside their functions.

- **2026-08-26 — `.gitignore`'s blanket `*.log` rule silently excluded `outcomes.log`.**
  Written into the initial scaffold before `outcomes.log` existed as a real state file the
  escalation workflow depends on being tracked (it commits state back to the repo across
  ephemeral CI runs — see Architecture in SPEC.md). Caught before the first push by previewing
  `git add -n .` and noticing the file missing from the list, not by assuming it would work.
  Fixed with a targeted `!outcomes.log` exception, same pattern already used for `.env.example`.
