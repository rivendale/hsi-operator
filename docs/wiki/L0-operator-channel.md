See the in-repo protocol (kept in lockstep):

https://github.com/rivendale/hsi-operator/blob/main/skills/hsi-operator/references/l0-channel.md

# L0 — the operator channel

L0 is not a UI. It is the **only authorized expenditure of operator attention**. `bin/hsi` is the current speaker. The skill prose is the protocol. Neither is a dashboard.

Siblings: [[Function-allocation]] · [[Honesty-protocol]] · [[The-loop]]

## Hierarchy (do not collapse it)

| Layer | Lives where | On L0? |
|---|---|---|
| **L0** | Chat / `hsi` stdout / the two doors | Yes. This is the channel. |
| **L1** | Item JSON | Only if they pull one item. |
| **L2** | `evidence` pointers | Only if they ask “show me.” |
| **L3** | Files, logs, diffs | Never. Steward holds the path. |

Quota: **three answerable questions per sitting**, plus one Door 2 conversation before work starts. A fourth item on L0 is a control-system fault.

## On the wire

**Required:** ranking rule said out loud; at most three questions (not status lines) with kind, 2–4 options, why-you, ignore-cost, their-cost; count held back plus `hsi … --all`.

**Allowed short:** one-line suggestion; hard external `BY` date; `signal` once #4 lands (`error` / `stale` beat `proposal`); Door 2's five questions when there is no setpoint.

**Forbidden:** facts, housekeeping, unused-thing maintenance, caution-APPROVE, dumps, reconstructed numbers as data, session recaps, a second copy of a fact that already has a path.

## Two doors, same channel

Door 1 is operations (prefer residual over new proposals once #3–#4 exist). Door 2 is setpoint-setting (#2). Do not multiplex in one sitting unless asked.

## Sitting, not session

Unanswered #1 stays #1. All three unanswered → those three only. Nothing needed → “Nothing needs you. That is the update.” Fourteen days unused → L0 is “this skill is furniture.”

Egress is a ledger row in their words with reasoning (#3). Chat is ephemeral.

Full failure modes and the canonical `hsi` frame: `skills/hsi-operator/references/l0-channel.md`.
