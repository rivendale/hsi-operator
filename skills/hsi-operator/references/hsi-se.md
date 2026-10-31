# HSI / SE shelf

What we took, what we refused, what arrived independently. Not a literature review.
The coding agent on #2 does not implement anything from this file.

## Took

- Human as a system element, not a user of a finished machine. NASA HSI Handbook v2.0 (2021).
- Function allocation between human and automation for AI-enabled systems. DAU HSI.
- In-service experience feedback. INCOSE / FlexTech HSI Primer Vol. 1.
- More automation → more HSI, not less. Endsley, Defense AT&L Jan–Feb 2016.
- Situation awareness as a *reading* of our fields (Endsley 1995): adapters perceive, `kind`/`why_you` comprehend, `if_ignored_30d` projects. Do not operationalise a 3-level scorer.
- SEBoK HSI one-sentence definition. DoD HSI Guidebook C1 2024 for domain names (manpower ≈ attention here).
- Parasuraman / Sheridan / Wickens (2000) types and levels of automation — parked in `allocation.md`. Not in `score()`.
- Honesty protocol from [ferdinandobons/startup-skill](https://github.com/ferdinandobons/startup-skill) (MIT).

Paul Iusztin, 15 Sep 2026: agent may research, scan, implement, QA, review; a human decides *what to build*, *shape*, and *what ships*. That is the person-test in one post. https://x.com/pauliusztin_/status/2099777741923004849

## Independent arrivals (steal a pattern, do not vendor)

Same failure mode, already solved in pieces. None of them close setpoint → residual. Wiring their CLIs in is enthusiasm.

- Handoff beats compact: [simplybychris/handoff-skill](https://github.com/simplybychris/handoff-skill), Amp “never compact”, [kunchenguid/compact-adviser](https://github.com/kunchenguid/compact-adviser) (already cited in `context-steward`), Hermes notes + searchable history rather than one summary.
- AC before build / skipped question is never a yes: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) planning + spec-driven (steal the checkable sentence, refuse the six-phase theatre); SureForge skill (Da7em, Sep 2026).
- Observation *masking*: tool output becomes a pointer. [muratcankoylan context-optimization](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering). That is L2.
- A skill that reports its own friction is `#5`, not a new product.

- Bainbridge (1983), "Ironies of automation": the more is automated, the less practice the
  operator keeps for the moment they must take over. The fourteen-day unused finding is the
  same failure seen from the tool's side.

## Refused

- Full seven-domain HSI program. We are not acquiring a vehicle.
- IMPRINT / ACT-R / digital human models.
- Learned ranker, weekly recap, 27-item board, second store for a fact that already has a path.
- [Arenukvern/skill_steward](https://github.com/Arenukvern/skill_steward) — repo charter/release stewardship. Different object. Name clash with `context-steward`; do not unify.
- Acontext / auto-written memory-as-skills. Second place for facts.
- Project-steward suites and HITL spec factories.

## Restricted three-body (a reading, not a solver)

Two-body HSI (human + machine, allocate, done) is integrable and is the lie everyone ships. Real work is restricted three-body: operator and agent are the primaries; the test particle is the *plant* (deadlines, other people, last week's setpoint, a second agent).

The general three-body problem has no closed form. That is why `score()` stays four printed terms. Do not put Jacobi constants or “Lagrange vectors” in the contract.

| Point | Here | Stability |
|---|---|---|
| **L1** between the masses | Shared autonomy, caution-APPROVE | Unstable. Do not park work here. |
| **L2** beyond the machine | Supervising a plant you cannot see | Unstable without L0. |
| **L3** | Operator out of the loop | Unstable. Fourteen-day unused skill. |
| **L4 / L5** | Standing rule + setpoint + ledger; `invalidated_by` has not fired | Quasi-stable. Cheap station-keeping. |

Δv is operator minutes this sitting. Residuals in that frame are setpoint − measured, attention quota, and who is blocked. The third mass stays *small* (one item, one sitting, one setpoint) or there is no cheap point.

Chaos is already Door 2: a vague large done is sensitive to initial conditions; shrink-done picks a smaller Hill sphere.

## Links

- NASA HSI Handbook v2.0: https://ntrs.nasa.gov/api/citations/20210010952/downloads/HSI%20Handbook%20v2.0%20092121_FINAL%20COPY.pdf
- DAU HSI: https://www.dau.edu/tools/dau-systems-engineering-brainbook/design-considerations/hsi
- SEBoK: https://www.sebokwiki.org/wiki/Human_Systems_Integration
- FlexTech HSI Primer Vol. 1: https://www.flextechchair.org/ewExternalFiles/HSI%20Primer%20Vol.%201%20v4.pdf
- DoD HSI Guidebook C1 2024: https://www.cto.mil/wp-content/uploads/2024/07/HSI-Guidebook-C1-2024.pdf
- Endsley 2016: https://www.dau.edu/sites/default/files/Migrate/DATLFiles/Jan-Feb2016/Endsley.pdf
- Parasuraman, Sheridan & Wickens 2000, "A model for types and levels of human interaction with automation", IEEE Trans. SMC Part A 30(3): https://doi.org/10.1109/3468.844354
- Endsley 1995, "Toward a theory of situation awareness in dynamic systems", Human Factors 37(1): https://doi.org/10.1518/001872095779049543
- Bainbridge 1983, "Ironies of automation", Automatica 19(6): https://doi.org/10.1016/0005-1098(83)90046-8

The two dau.edu links above are not link-checked: dau.edu redirects to waru.edu, which answers
403 to automated clients, so CI excludes the domain (see `.github/workflows/evals.yml`). Both
answered 403 to a plain request on 2026-10-31. A person with a browser can still open them. The DOI
links are checked in CI by asking doi.org for each one's citation record, because the
publisher pages behind them refuse link checkers too.
