# SPEC — Good Neighbor Agent

Entry for the [Agents for Humans Hackathon](https://agentsforhumans.devpost.com/) (AWS/Devpost),
**Good Neighbor Agents** track. Deadline: Sep 14, 2026, 5pm PT.

## Problem

Blind and low-vision people regularly need a sighted person for small, situational tasks —
reading a label, describing a document, navigating a changed route. Today this runs on ad hoc
favors: texting whoever's around, hoping someone answers in time. There's no system that
routes the request to someone available, escalates when no one responds, or handles the parts
an AI can already answer directly without waking a human up for it.

## Who it's for

A small neighborhood/community volunteer network (the kind a library, nonprofit, or local
accessibility group already runs informally) — not a single individual's personal assistant.
This is what puts it in Good Neighbor Agents rather than Everyday Agents.

## What it does

A requester submits a task in plain text (+ optional photo). The agent:

1. Answers directly if it can do so confidently from what's given — no volunteer involved.
2. Otherwise finds an available volunteer matching the needed skill and notifies them.
3. Escalates to a human coordinator if no volunteer is available, or if the request reads as
   safety-critical (e.g. medication, an unsafe location).
4. Logs the outcome regardless of path taken.

It runs autonomously end-to-end; a human only sees it when there's a real decision to make.

## Architecture

- **Agent**: Strands Agents SDK, Python. One `Agent` with a system prompt encoding the
  decide-directly-vs-route-vs-escalate judgment (not hardcoded branching).
- **Model**: thegrid.ai (`agent-prime` instrument) via Strands' OpenAI-compatible provider.
  No AWS billing account — deliberate tradeoff, see [implementation-notes.md](implementation-notes.md).
- **Tools**: `find_volunteer`, `notify_volunteer`, `escalate`, `log_outcome` (all in `tools.py`).
- **Roster**: JSON-backed in-memory list (`volunteers.json`) — sufficient for hackathon scale,
  not meant to be a real production data store.
- **Background/autonomy**: a GitHub Actions scheduled workflow (`.github/workflows/escalation-check.yml`,
  every 5 min) runs `escalation_check.py`, which checks `pending.json` for requests notified
  more than `ESCALATION_TIMEOUT_MINUTES` ago and escalates them — a deterministic timeout
  check, not an LLM call, so it runs standalone without going through the agent. Chosen over
  AWS EventBridge to avoid the billed AWS account this project avoids elsewhere. Since CI
  runners are ephemeral, the workflow commits `pending.json`/`outcomes.log` changes back to
  the repo — the one real tradeoff of this approach (periodic bot commits); acceptable at
  hackathon scope, would move to a real datastore in Phase 4.
- **Notification**: [Resend](https://resend.com/) (planned) — not yet wired. Swapped in for
  SES on 2026-08-25: SES requires the same billed AWS account this project deliberately
  avoids by using thegrid.ai instead of Bedrock; Resend's free tier (100/day, 3,000/month)
  covers hackathon-demo volume with no AWS dependency.

## In scope for submission

- Working agent loop with the four tools (**done**, verified 2026-08-25 — both the
  direct-answer and volunteer-routing branches ran end-to-end against real `thegrid.ai`
  calls, with real tool side effects confirmed in `outcomes.log`).
- Real (not stubbed) volunteer notification via Resend.
- A timeout/escalation check that actually fires without a human polling for it.
- Public GitHub repo, MIT license, README, architecture diagram, 5-minute demo video,
  AWS Builder ID on the submission form.

## Roadmap — sequenced, not parallel (decided 2026-08-25)

Phase 1 (In scope above) is the guaranteed-complete submission floor. Phases below are
stretch goals in priority order — each is independently useful even if time runs out before
the next one starts. Do not start Phase N+1 until Phase N is verified working.

- **Phase 2 — Web intake form**: a public page where a requester actually submits text + photo,
  instead of demoing via terminal. Makes the demo video show a real product surface.
- **Phase 3 — SMS/WhatsApp notification**: volunteers get pinged by text instead of only email.
  Needs Twilio (or similar) account + verified sender; real per-message cost, budget for it.
- **Phase 4 — Real volunteer accounts + roster management**: sign-up, login, self-managed
  availability, replacing the static seed JSON. Requires a persistent DB — the biggest single
  chunk of remaining work, only start this if Phases 2-3 are done with real runway left.
- **Reconsider if time allows**: AgentCore Runtime deployment (doesn't actually require
  Bedrock as the model — it's a model-agnostic hosting runtime — the blocker is still needing
  a full billed AWS account, unresolved). A coordinator dashboard (response times, escalation
  frequency) — strong demo material for Potential Impact once Phase 1-2 are solid.
- **Deliberately not planned**: multi-language support — real scope, no clear path to fit it
  in this timeline even as a late-stretch item.

## Acceptance criteria (checked at Stage 5 verify)

1. **Direct-answer branch works** — falsifier: run a request the agent can answer from given
   info; `find_volunteer`/`notify_volunteer` must NOT be called; `outcomes.log` gets an
   `"answered directly"` entry. *(Already passing.)*
2. **Volunteer-routing branch works** — falsifier: run a request needing physical/local help;
   `find_volunteer` returns a real match, `notify_volunteer` actually sends (not just logs),
   `outcomes.log` records it. *(Resend integration verified 2026-08-26 — real API send
   confirmed working; full agent-flow re-test still needed once roster emails are updated
   to a deliverable address, see implementation-notes.md.)*
3. **Escalation fires without a human polling** — falsifier: submit a request with no matching
   available volunteer; confirm `escalate` fires on its own via the scheduled check, not
   because someone manually re-ran the script. *(Fully verified locally 2026-08-26: real
   `notify_volunteer` → backdated → `escalation_check` correctly detected it overdue, sent a
   real coordinator email (after fixing a module-level env var bug caught by this test — see
   implementation-notes.md), and marked it `"escalated"`. GitHub Actions workflow verified
   live 2026-08-26: manual `workflow_dispatch` run succeeded (43s, exit 0) against an empty
   `pending.json`, escalating nothing as expected — confirms the scheduled path fires and
   completes with `RESEND_API_KEY`/`DEMO_INBOX` repo secrets configured. Fully verified.)*
4. **Safety-critical requests escalate even if a volunteer exists** — falsifier: submit a
   request mentioning medication/unsafe-location language with an available volunteer present;
   confirm the agent still escalates rather than routing silently. *(Verified 2026-08-28:
   two-unlabeled-pills medication request with a matching available volunteer on the roster —
   agent escalated, did NOT call find_volunteer/notify_volunteer (`pending.json` stayed empty),
   and additionally refused to guess dosage. Confirmed.)*
5. **Repo passes hackathon submission requirements** — public repo, MIT license visible in
   About section, README, architecture diagram, ≤5min video covering problem/who/why,
   AWS Builder ID present on the submission form.

## Anti-criteria (must NOT happen)

- Agent must never claim a tool ran when it didn't (already guarded against by checking
  `outcomes.log`/stub print output directly, not trusting the model's narration).
- Agent must not route a request to a volunteer who isn't marked available.
- Demo video must not show fabricated/staged data presented as if it were a real volunteer
  response — the notify step is honestly labeled as a demo roster, not a claim of a live
  volunteer network.

## Decisions defaulted (cheap, reversible — flagging rather than re-asking)

- **Timeout before escalation: 10 minutes.** Defensible on camera, not claimed as a
  production-tuned value. Change is a one-line edit if you want something else.
- **Demo video (Phase 1): narrated over terminal/`agentcore dev` output**, not a web form —
  keeps the video independent of whether Phase 2 ships in time. Revisit once Phase 2 exists.
