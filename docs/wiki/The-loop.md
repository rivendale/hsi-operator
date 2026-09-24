# The loop (issues #1–#8)

Parent: https://github.com/rivendale/hsi-operator/issues/1

The skill ranks three, elicits done, and now records answers and manual invalidations in a ledger. HSI as systems engineering is a **negative-feedback regulator**: compare the world to a human-set setpoint, pass only the residual to [[L0-operator-channel]]. The ledger adapter surfaces recorded invalidations; it does not detect when conditions fire.

| # | Issue | Loop part | Status |
|---|---|---|---|
| 2 | [Setpoint JSON + `hsi done`](https://github.com/rivendale/hsi-operator/issues/2) | Setpoint | **landed 2026-09-21** | |
| 3 | [Ledger + `hsi record`](https://github.com/rivendale/hsi-operator/issues/3) | Actuator write-back | **landed 2026-09-24** |
| 4 | [`signal` + residual/stale score](https://github.com/rivendale/hsi-operator/issues/4) | Error channel | **landed 2026-09-24** |
| 5 | [Unanswered inventory + 14-day unused](https://github.com/rivendale/hsi-operator/issues/5) | Bandwidth | 14-day unused **landed** ([#23](https://github.com/rivendale/hsi-operator/pull/23)); inventory waiting |
| 6 | [Steward typed blocks](https://github.com/rivendale/hsi-operator/issues/6) | State estimator | waiting |
| 7 | [One real adapter](https://github.com/rivendale/hsi-operator/issues/7) | Sensor | **landed 2026-09-24** |
| 8 | [Allocation + HSI shelf](https://github.com/rivendale/hsi-operator/issues/8) | Policy | **landed 2026-09-21** |

Do not implement what remains of #5 and #6 from wiki prose. Fit the frame on [[L0-operator-channel]] or the issue is wrong.
