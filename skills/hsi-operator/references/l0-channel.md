# L0 — the operator channel

L0 is not a UI. It is the **only authorized expenditure of operator attention**.
Everything else in the stack exists to keep this channel narrow, answerable, and
honest. `bin/hsi` is the current speaker. The skill prose is the protocol. Neither
is a dashboard.

Sibling: what is the human's versus the machine's is `allocation.md`.
Claim labels: `honesty-protocol.md`.
Loop map: issues #1–#8. Three-body reading: `hsi-se.md`.

---

## The hierarchy (do not collapse it)

| Layer | Lives where | On L0? |
|---|---|---|
| **L0** | Chat / `hsi` stdout / the two doors | Yes. This is the channel. |
| **L1** | Item JSON (`question`, `options`, `why_you`, …) | Only if they pull one item. |
| **L2** | `evidence` pointers (`file:line`, a command) | Only if they ask “show me.” |
| **L3** | Files, logs, diffs, credential *locations* | Never. Steward holds the path. |

The operator lives at L0. The loop *computes* with L2. L3 is never in the prompt
unless pulled. A summary that replaces L3 is a sensor failure.

**Mask tool output to a pointer.** That is L2. Do not paste the dump. Observation
masking arrived independently in context-engineering skills; we already required it.

A list of twenty-seven is a list of zero. The quota is **three answerable questions
per sitting**, plus one Door 2 conversation *before* work starts. A fourth item on
L0 is a control-system fault, not a product idea.

---

## What is allowed on the wire

An L0 frame is a **question only the operator can close**, plus the minimum
structure needed to close it in one sitting.

**Required**

1. The ranking rule, said out loud. A hidden ranking is a judgement they cannot audit.
2. At most three items, each with:
   - `kind` — `DECIDE | APPROVE | EXECUTE | TASTE`
   - a **question**, not a status line
   - **2–4 options** with consequences (L1 leaking one level — intentional)
   - why it needs them, not the machine
   - cost of ignore at 30 days
   - cost to them: minutes / a decision / money / a conversation
3. How many were held back, and the one keystroke to see them (`hsi … --all`).
   Held back is still in the system. It is not L0.

**Allowed, short**

- `I'd suggest:` one sentence
- `BY <hard external date>` only — soft revisits are not deadlines
- `signal` once #4 lands: `error` / `stale` / `proposal`. Error and stale outrank proposal.
- Door 2's five questions, in order, when work has no setpoint

**Forbidden** — these are how the channel dies

- Facts. An item asking a person for a fact is a search you skipped.
- Housekeeping dressed as priority.
- Maintenance of something nobody uses. That is a deletion *proposal*, framed or dropped.
- Permission-seeking for work the machine can do inside a standing rule.
- Tool output, diffs, stack traces, analysis beyond 2–4 options.
- Reconstructed numbers presented as data (`[RECONSTRUCTED]` does not ship on L0 until re-measured — #6).
- A recap of the last session.
- A second copy of a fact that already has a path.

If the machine needed a fact, it searches and says what it answered from. That
sentence may appear as context *for a real question*. It cannot *be* the question.

---

## Two doors are two modes of the same channel

**Door 1 — “how can I help”** is the error channel in operations. After #3–#4 exist
it should prefer `error` and `stale` over fresh `proposal`. A board of new ideas
while last week's setpoint is false is L0 used as a suggestion box.

**Door 2 — “what does done mean”** is setpoint-setting (#2). Still L0: five
questions, operator's words, shrink-done. Not a spec workshop. When criteria are
hard to state, make the goal smaller, then stop.

Do not multiplex them in one sitting unless the operator asks. Door 2 before build.
Door 1 when they have attention to give. Mixing them is how Door 2 becomes item four
on a triage list.

---

## The unit of work is a sitting, not a session

L0 is budgeted per **sitting** (one stretch of human attention), not per agent
context window. #5 instruments this. The rules, once they exist:

- Last sitting's unanswered #1 stays #1. New work fights for slots 2–3.
- If all three are unanswered, L0 is those three. `--all` still exists.
- If nothing needs them: print **“Nothing needs you. That is the update.”**
  Silence reads as a stalled assistant.
- If they have not answered in 14 days, L0 is one item: this skill is furniture.
  Adding adapters that week hides the finding the README already named.
- After the three, one optional question: “Were these the right three?” A no is a
  correction to the ranker, stored off-channel. Not NASA-TLX.

Do not add a fourth item because the week is busy. Busy is when the cap matters.

---

## Ingress and egress

**Ingress** — only items that pass the person-test in the SKILL, after adapters and
agents have already:

- dropped closed / not-theirs / empty (`adapters/jsonl-tasks/collect.py`)
- refused to invent `why_you` and `options` in the adapter
- filled options in an agent pass, *or* left them empty rather than hallucinating
- attached `evidence` as a pointer, not a paste
- labelled `signal` if known (#4)

**Egress** — a closed question, in their words, with reasoning, dated, with
`invalidated_by` (#3). Chat is ephemeral. The ledger is the actuator. “Yeah do that”
with no reasoning is an L0 failure even if the work proceeds.

Pulling L1/L2 is not egress. It is the operator opening a hatch. The hatch is one
keystroke (`--why ID`, `--all`, run the evidence command). It must not dump L3 into
the next model turn unless they asked.

---

## Failure modes

1. **Status-line capture.** “Vendor renews 14 Oct” is not L0. “Renew at $18k, drop
   to free, or export-then-drop?” is.
2. **Option explosion.** Five options is the machine refusing to decide what is on
   the table. Cap 2–4; the rest is L1 behind `--why`.
3. **Caution-APPROVE.** “May I run the tests?” is not APPROVE. APPROVE is
   irreversible or outward-facing.
4. **Taste mis-filed as DECIDE.** UI/UX is TASTE. A generated A/B is not taste;
   their judgement of quality is.
5. **L0 as log.** A paragraph before the first question is the plant leaking.
   One line of ranking rule, then questions.
6. **Re-ask.** A settled `item_id` whose `invalidated_by` has not fired must not
   reappear. Report the defect once. Do not board it.
7. **Reconstructed plant.** `[RECONSTRUCTED]` evidence does not score and does not
   ship on L0 until re-read or re-measured.

---

## What L0 is not

Not a dashboard. Not a chat personality. Not a briefing. Not an agent-swarm status
board. Those maximize *displayed* situation awareness and destroy *usable*
situation awareness.

Do not “build an L0 component.” Constrain every other layer so L0 can stay short.

- Adapters: candidates only.
- Agents: frame options, never board facts.
- Steward: pointers in L3.
- Ledger: egress off-channel.
- Ranker: printed arithmetic. `--why` remains the audit.
- Sitting file: memory of the quota (#5).

If a change makes L0 longer so the machine can feel thorough, it is the same defect
as an assistant that approves everything.

---

## Canonical frame

What `bin/hsi` already almost prints. Keep this density even when an agent is
speaking instead of the CLI.

```
3 of 11 thing(s) need you. Ranked by: hard deadline first,
then irreversibility, who is blocked, and the cost of doing nothing for 30 days.

1. [DECIDE] Renew the analytics vendor at $18k/yr, drop to free, or export then drop?
      BY 2026-10-14
      needs you: money, and whether the history is worth keeping
        - Renew — $18k/yr, history kept, auto-renews again
        - Free tier — $0, 90-day retention, history deleted
        - Export then drop — $0 after a month, history as our files, ~2 days
      I'd suggest: Export then drop, unless anyone queried older than 90 days this year.
      if ignored: Auto-renews 2026-10-14 and the decision is made for you.
      money
      evidence: contracts/analytics-2025.pdf:4

2. [TASTE] …
3. [EXECUTE] …

8 more held back, one keystroke away:  hsi items.json --all
```

Door 2 is the same density: five questions, answers in their words, one checkable
sentence, out of scope, what would change it. See `examples/done-criteria.example.md`
and, once #2 lands, the setpoint JSON beside it.

---

## What this file does not authorize

Take your assignment from the issue tracker, not from this page — it ships with the skill
and cannot know what has landed. This file is protocol. It does not add fields to
`hsi --schema`. Do not implement sitting files, `signal`, or the ledger from here. When those issues land, they must still fit this frame — if they make
L0 longer, the issue is wrong, not the frame.
