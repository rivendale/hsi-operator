In-repo: https://github.com/rivendale/hsi-operator/blob/main/skills/hsi-operator/references/allocation.md

# Function allocation

The person-test in SKILL.md *is* allocation. Written here so a ranker can name a defect without inventing policy.

```
FACT                         → machine (a search you skipped)
HOUSEKEEPING                 → machine, or a deletion proposal
TASTE / RISK / MONEY /
  LEGAL / RELATIONSHIP       → human
IRREVERSIBLE outward action  → human APPROVE, then machine EXECUTE
HANDS (login, signature,     → human EXECUTE
  phone)
```

Kinds on [[L0-operator-channel]]: `DECIDE | APPROVE | EXECUTE | TASTE`. No fifth kind.

| Defect | On L0? |
|---|---|
| Human asked for a fact | **No.** Search; say what you answered from. |
| Machine shipped UI without TASTE | **Yes**, TASTE / `error`. |
| Permission inside a standing rule | **No.** Delete the ask. |
| Setpoint check fails | **Yes**, `error` (#2, #4). |
| `invalidated_by` fired | **Yes**, `stale` (#3, #4). |

Sheridan / Parasuraman LOA numbers do **not** go in `score()`. Raise autonomy only on a measured miss-rate. Parked so it is not rediscovered as a feature.
