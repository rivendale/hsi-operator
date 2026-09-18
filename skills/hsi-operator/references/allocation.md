# Function allocation

The person-test in `SKILL.md` *is* HSI function allocation. Written down here so a
ranker or adapter can name a mis-allocation without inventing policy.

Sibling: what may reach the operator, and at what density, is `l0-channel.md`.
Citations and the three-body reading: `hsi-se.md`.

**A skipped question is never a yes.** Door 2 exists so silence cannot pass as
acceptance. SureForge / honesty; not a new phase gate.

```
FACT                         → machine (a search you skipped)
HOUSEKEEPING                 → machine, or a deletion proposal
TASTE / RISK / MONEY /
  LEGAL / RELATIONSHIP       → human
IRREVERSIBLE outward action  → human APPROVE, then machine EXECUTE
HANDS (login, signature,     → human EXECUTE
  phone)
```

Four kinds reach L0, and nothing else does:

- **DECIDE** — preference or risk appetite
- **APPROVE** — gated on a human; usually irreversible or outward-facing
- **EXECUTE** — only they have the hands
- **TASTE** — how it should look, read, or feel. UI/UX belongs here.

## Mis-allocation is a loop defect, not a fifth kind

`kind` stays those four. Once #4 exists, say *why the item is on the board* with
`signal: proposal | error | stale`.

| Defect | What it is | On L0? |
|---|---|---|
| Human asked for a fact | sensor failure | **No.** Search, say what you answered from. |
| Machine shipped UI without a TASTE call | allocation failure | **Yes**, TASTE / `error`. |
| Permission asked inside a standing ledger rule | caution dressed as APPROVE | **No.** Delete the ask. |
| Setpoint `check` exits non-zero | residual (#2, #4) | **Yes**, original kind / `error`. |
| `invalidated_by` fired | standing answer no longer licensed (#3, #4) | **Yes**, `stale`. |

## Dynamic autonomy — parked

Sheridan / Parasuraman levels of automation are the named prior art for “machine
proposes options” vs “machine acts unless vetoed.” Do **not** put LOA numbers in
`score()`. If autonomy is ever raised, raise it on a measured miss-rate for that
kind, same spirit as `repo-triage` (measured gap or no). That sentence lives here
so it is not rediscovered as a feature request.

## What this page is not

Not a seven-domain DoD HSI matrix. Not IMPRINT. Not a second issue tracker.
Borrow the integrator habit — trade attention against irreversibility — not the
reporting stack. External citations live in `hsi-se.md`.
