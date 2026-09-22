# The loop (issues #1–#8)

Parent: https://github.com/rivendale/hsi-operator/issues/1

The skill is an open-loop filter today (rank three, elicit done). HSI as systems engineering is a **negative-feedback regulator**: compare the world to a human-set setpoint, pass only the residual to [[L0-operator-channel]].

| # | Issue | Loop part | Status |
|---|---|---|---|
| 2 | [Setpoint JSON + `hsi done`](https://github.com/rivendale/hsi-operator/issues/2) | Setpoint | **landed 2026-09-21** | |
| 3 | [Ledger + `hsi record`](https://github.com/rivendale/hsi-operator/issues/3) | Actuator write-back | waiting |
| 4 | [`signal` + residual/stale score](https://github.com/rivendale/hsi-operator/issues/4) | Error channel | waiting |
| 5 | [Unanswered inventory + 14-day unused](https://github.com/rivendale/hsi-operator/issues/5) | Bandwidth | waiting |
| 6 | [Steward typed blocks](https://github.com/rivendale/hsi-operator/issues/6) | State estimator | waiting |
| 7 | [One real adapter](https://github.com/rivendale/hsi-operator/issues/7) | Sensor | waiting |
| 8 | [Allocation + HSI shelf](https://github.com/rivendale/hsi-operator/issues/8) | Policy | **landed 2026-09-21** |

Do not implement #3–#7 from wiki prose. Fit the frame on [[L0-operator-channel]] or the issue is wrong.
