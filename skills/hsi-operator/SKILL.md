---
name: hsi-operator
description: Use when the operator asks "how can I help", "what needs me", or "what do you need from me" — and use at the START of new work to establish what done means before building. Keeps a human at the strategic level: decisions, approvals, taste and UI/UX calls, and acceptance criteria.
license: MIT
---

# hsi-operator

Human-systems integration for agent work. **Two doors.**

| door | when | what it does |
|---|---|---|
| **`how can I help`** | the operator has attention to give | surfaces the **3** things that most need a person, each as an answerable question |
| **`what does done mean`** | BEFORE work starts | elicits acceptance criteria in one checkable sentence |

Neither is subordinate. Most failures come from the second being skipped.

---

## DOOR 1 — "how can I help"

### The test for what reaches a person at all

> **Does the answer depend on the operator's preference, intent, risk appetite,
> money, relationships, legal exposure, or taste?**

**Yes** → it is theirs. **No** → answer it yourself and say what you answered from.

Four kinds reach them, and nothing else does:

- **DECIDE** — depends on their preference or risk appetite
- **APPROVE** — an action gated on a human, usually irreversible or outward-facing
- **EXECUTE** — only they have the hands: a login, a signature, a phone call
- **TASTE** — how it should look, read or feel. **UI/UX belongs here and is
  routinely mis-filed as a decision.** A taste call is not a preference between
  options someone else generated; it is the operator's judgement about quality.

### HARD RULE: surface three

**A list of twenty-seven is a list of zero.** Return the **3** whose answers unblock
the most, and make the rest one keystroke away — never gone, never first.

Say the ranking rule out loud every time, because a hidden ranking is a judgement the
operator cannot audit:

1. **Irreversibility** — can this be undone next week?
2. **Who is blocked** — a person or agent stopped, waiting
3. **Cost of inaction at 30 days** — money, legal exposure, a forfeited benefit
4. **Hard external deadlines override all of the above** and go first

### Each item is a QUESTION, not a status line

A status line makes them do the work of turning it into a decision. Give them:

- the **question**, phrased so it can be answered in a sentence
- **2–4 options** with the consequence of each, and a recommendation if you have one
- **why this needs them** and not you
- **what happens if it is ignored** for 30 days
- **what it costs them**: minutes, a decision, money, a conversation
- **evidence** — a file:line or a command they could run

### What must NEVER reach them

- Anything retrievable from the record. **An item asking a person for a FACT is a
  search you skipped.**
- Your own housekeeping dressed as a priority — index tidying, status files, cleanup.
- Maintenance of something nobody uses. That is a **deletion proposal**, not a question.
- Work you could do and are seeking permission for out of caution.

---

## DOOR 2 — "what does done mean"

Run this **before** building, not at the end. Five questions, in order.

1. **Who uses this, and when?** If the honest answer is "nobody yet", say so now.
   Most wasted work fails here and passes every other test.
2. **What does the finished thing let you do that you cannot do today?**
3. **What would make you say "that is not what I wanted"?** The fastest route to
   taste, because people describe wrongness far more precisely than rightness.
4. **One checkable sentence: how do we both know it is done?** It must be
   **external to the model** — a command that exits zero, a number that moves, a
   person who uses it. "It looks good" is not checkable.
5. **What is explicitly OUT of scope?** Write it down; this is what stops the work
   growing quietly.

### Write it as a setpoint, and cite it before starting

The five answers go in one JSON file, the **setpoint**. `hsi --schema` prints the shape;
`examples/setpoint.example.json` in the repo is the worked example as a file.

`id` · `who` · `when` (1) · `enables` (2) · `wrong_if` (3) · `done` + `check` (4) ·
`out_of_scope` (5) · `invalidated_by` · `words` · `date` · `basis`

Two fields are new: an **id** to cite, and **words**, the request as they first put it,
verbatim. The rest is this page as fields: `check` is question 4's command, number or
person, and `invalidated_by` is the stale-answer rule below, a condition and never a timer.

```
hsi done setpoint.json    # prints the five answers; exit 2 if done has no check
```

**The interlock: no work starts without a setpoint id.** Cite the id before building. No
id means Door 2 has not run. Exit 2 means it ran and did not produce a checkable done, and
the move is to shrink done, not to start anyway. This is a rule you keep, not a lock:
nothing blocks a keystroke, and nothing should. `hsi done` checks the *shape* of the check;
whether it would prove anything is still read by a person.

### The bias: SHRINK the definition of done

When the criteria are hard to state, the answer is usually a **smaller** done, not
more planning. A vague large goal becomes a specific small one — not a specification
for the large one.

### SMART, without the theatre

The five questions above already produce Specific, Measurable, Achievable, Relevant
and Time-bound. Do not make anyone fill in an acronym. If one is genuinely missing,
ask for that one.

---

## Write the answer down, with its reasoning

**The compounding value is not the questions. It is that nothing gets asked twice.**

Every answer is recorded with:
- the question as asked, and the answer **in the operator's own words**
- the reasoning, if given — this is what makes future calls match their taste
- the date

A settled question that returns is a defect. So is an answer recorded without the
reasoning, because the next session inherits a verdict it cannot apply to a
neighbouring case.

## Keep a stale answer from ruling forever

An answer was true of the world when it was given. Record **what would change it**,
and re-ask when that changes rather than on a timer.

## Label the basis of what you say

`[Data]` sourced · `[Estimate]` calculated, assumptions stated · `[Assumption]`
unverified · `[Opinion]` your judgement. Never present an estimate as data. Full
discipline in `references/honesty-protocol.md`, which also covers stating an absence
rather than omitting a section, and giving a verdict rather than a list of
considerations.

## Do not let this become another thing nobody opens

If the operator has not used it in two weeks, **that is the finding** — report it
rather than adding features. Instrument that, and say so.
