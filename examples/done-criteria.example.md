# Worked example — "what does done mean"

This is the human side of `setpoint.example.json`. Same answers, same id: the markdown is
how a person reads Door 2, the JSON is what work cites and is checked against.

**Request as received:** *"can we build a dashboard for the team"*

That is not buildable. It is a direction. The five questions turn it into work.

| question | answer |
|---|---|
| Who uses it, and when? | *"Me, Monday mornings, before the standup."* — one person, one moment. Not "the team". |
| What does it let you do that you can't today? | *"Stop asking three people what shipped last week."* |
| What would make you say "that's not what I wanted"? | *"If I still have to open Jira to understand it."* |
| One checkable sentence for done | **"On Monday I can answer 'what shipped' without opening another tab."** |
| Explicitly out of scope | Anything about the future. No roadmap, no burndown, no estimates. |

**Setpoint `monday-shipped`, 2026-09-18.** The check is a person, not a test suite: at
Monday standup, they answer "what shipped" with no other tab opened. Rows 1 to 4 are the
requester's own words, quoted; out of scope and the check are written from them. Basis
[Data], source: the requester.

```
hsi done examples/setpoint.example.json
```

**What changed.** "A dashboard for the team" would have taken weeks and been opened
twice. The real thing is one page, one reader, one moment, and the acceptance test is a
sentence anyone can check on a Monday.

**The bias in action.** Nobody made the goal more rigorous. They made it *smaller*. That
is the move when criteria are hard to state.

**What would change the answer**, recorded so it is not re-asked on a timer: if standup
moves, or if a second person starts reading it, re-run this.
