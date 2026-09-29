# Eval and hillclimb, with two gates a person holds

**Draft, to be finalized after the first run.** Written 2026-09-29 from Anthropic's method post and
one run being set up. No result is in yet.

The method comes from
[Automating eval design and hillclimbing](https://claude.dev/blog/automating-eval-design-and-hillclimbing/)
(Lance Martin, 2026-09-28): Claude "builds the eval inside your codebase, and pauses for approval
at specific points." Cases for a detector are built as in
[`planted-defect-evals.md`](planted-defect-evals.md).

## Gate 1: before anything runs

- The person approves the **cases**, with every input shown on one page, and the **grading**, from
  a handful of graded pilot cases: would they have scored any of them differently?
- The person sees the **measured cost of one full pass** before approving a budget.
- Changing a case or the grader after approval needs a new approval.

## The loop (no person needed)

- Work on a new branch, one change per round: a model, an effort level, a prompt edit, or a
  harness change.
- Split the cases into train and test, and let the hillclimber read train only. In the post's
  words: "If the train set scores improve while the test set scores stay flat, then that is a
  common overfitting warning sign." Drop that change.
- Run the baseline twice first. The post's checks during the baseline: run the grader twice on the
  same output and report whether the verdict changed, and look for timeouts, API errors and cut-off
  answers "to ensure infrastructure noise doesn't pass as model variance." Before the first round,
  confirm the eval's noise is smaller than the smallest improvement you would act on; if not, add
  repetitions or cases.
- Run each setting at least three times. A stochastic process needs repeats, not a pass or fail: in
  one review, the same probes passed 3 of 8 times across personas for one model, and the first two
  lucky runs had made pinning that model look obvious.
- Walk a staircase from the cheapest plausible setting ([`choosing-effort.md`](choosing-effort.md)),
  not a full grid.
- Run the eval in the same context as production (same instruction files, same working
  directory), with the answers out of reach (tools off).
- "Never paste failures into the prompt."
- Stop after two or three rounds with no gain, or when no single change could beat the noise.

## Gate 2: before anything merges

The report comes first and says three things: what changed at each step and how accuracy and cost
per task moved; which cheaper setups got things wrong, and where; which sentences left or entered
the prompt. It records quality regressions even when a setting is cheaper. If the gain is within
noise, the report says so and recommends against merging. Nothing merges until the person confirms.

## Keep the eval honest about itself

- Test actions and artifacts, not instruction length or keywords, with identical settings on both
  arms. [threejs-game-skills](https://github.com/majidmanzarpour/threejs-game-skills) (MIT) says the
  same about its own pack in `skills/threejs-game-director/references/workflow-evaluations.md`,
  read at commit 8286774 on 2026-09-29, and adds: "Record quality regressions even if the candidate
  is faster or uses fewer tokens."
- Delete a benchmark that never changes a decision.
