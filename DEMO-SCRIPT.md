# Demo video script — Good Neighbor Agent

Format: screen recording of terminal output, narrated over it. Target ≤5 min. No web form —
Phase 2 (intake UI) hasn't started, this demos the Phase 1 agent loop directly.

Before recording: confirm `DEMO_INBOX` in `.env` is `kazani@disroot.org` (Resend sandbox only
delivers to the account's own registered address without a verified domain — see
implementation-notes.md). Have the inbox open in a second window/tab so received emails are
visible on screen when they arrive. Also open the GitHub Actions run history tab for segment 4.

---

## 0:00–0:45 — Problem, audience, why it matters (talking head or voiceover over title card)

- **Problem**: Blind and low-vision people run into small physical-world tasks all day that
  need a sighted human for a moment — reading a label, filling a form, checking a street sign.
  Volunteer networks exist for this, but coordinating them is manual: someone has to notice
  the request, figure out who's free, follow up, and know when to step in themselves.
- **Who it's for**: the volunteer network's coordinators and the neighbors they serve — the
  agent is the dispatcher, not a replacement for the volunteers.
- **Why it matters**: most of these requests are simple enough the agent can just answer them.
  The ones that aren't need a human — and someone has to catch it if nobody responds in time.
  That triage, done reliably and without dropping anything, is the actual product.

## 0:45–1:30 — Architecture, 30,000 ft (show README diagram)

- Screen: the Mermaid diagram in README.md.
- One sentence per lane: "Requests come in, the agent decides — answer directly, route to a
  volunteer, or escalate. A separate background job checks every five minutes for anything
  that timed out and escalates that too, even with no human watching."
- Name the stack fast, don't dwell: Strands Agents SDK, thegrid.ai for the model, Resend for
  email — no AWS billing account required for any of it.

## 1:30–2:15 — Criterion 1: direct-answer branch

- Run the agent with a request it can answer outright (e.g. the Metformin dosage example
  already in `agent.py`'s `__main__` block, or a similarly self-contained question).
- Narrate while it runs: "No volunteer gets bothered for something the agent already knows."
- Show `outcomes.log` afterward — point at the new line, note `find_volunteer` /
  `notify_volunteer` were never called.

## 2:15–3:15 — Criterion 2: volunteer routing with a real email

- Run a request that needs a human in the physical world (something from `volunteers.json`'s
  skill list — e.g. navigation help).
- While it's running, narrate the tool calls as they print: `find_volunteer` matches someone,
  `notify_volunteer` sends.
- Cut to the inbox — show the real email arriving. This is the moment that proves it's not
  a mock: an actual message landed in an actual inbox.
- Show `pending.json` now has an entry for this request.

## 3:15–4:00 — Criterion 3: autonomous escalation on timeout (GitHub Actions)

- Explain: "If nobody answers in ten minutes, the agent doesn't wait around — a background
  job on GitHub Actions checks every five minutes and escalates on its own, no LLM call at
  the time of the check."
- Show the Actions run history: a real past run of `escalation-check.yml`, green, with the
  step log showing it found the overdue entry from the previous segment and escalated it.
- Cut to inbox: the escalation email to the coordinator.
- Point at the commit it made back to the repo (`pending.json`/`outcomes.log` updated) —
  one line: "the CI runner is ephemeral, so it persists state by committing it back."

## 4:00–4:40 — Criterion 4: safety-critical escalates even with a volunteer available

- Run a request that's safety-critical (medication, an unsafe situation) where a volunteer
  *is* available and matched.
- Narrate: "Even though someone could help, this isn't a wait-and-see situation — the agent
  escalates straight to a human coordinator instead of routing and hoping."
- Show the escalation email + the `outcomes.log` entry confirming the outcome was `escalated`,
  not `volunteer: ...`.

## 4:40–5:00 — Close

- One line on what's next (Phase 2: web intake form; not built yet, sequenced deliberately —
  shipping a small verified thing beats a bigger unfinished one).
- Repo link on screen: github.com/kazani-351/good-neighbor-agent.

---

## Recording notes

- Filter the httpcore2 async-cleanup traceback from any raw terminal capture if it appears —
  it's a benign upstream warning after the correct output, not part of the story (see
  implementation-notes.md). Cut around it or crop it out in editing.
- Keep terminal font large enough to read at 1080p compressed for YouTube/Devpost embed.
- If a live run doesn't complete in time to record smoothly, it's fine to record the run once
  unnarrated to capture clean footage, then re-record narration over the replay — the criteria
  were already proven live per HANDOFF.md; this video is documentation, not a new test.
