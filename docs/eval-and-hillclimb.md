# Eval and hillclimb, with two gates a person holds

Written 2026-09-29 from Anthropic's method post, before the first run; the first run's lessons
are in [What the first run showed](#what-the-first-run-showed).

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
- **Check a public benchmark before a claim leans on it, and prefer your own eval.** Epoch AI's
  Benchmark Reviews launched in September 2026 with 15 benchmarks reviewed: 4 verified, 9 found
  flawed (SWE-Bench Verified, SWE-Bench Pro, Terminal-Bench 4.0.0 and DeepSWE v1.1 among them)
  and 2 with too little information to judge (counts as reported at launch; check the current
  list). A score on a flawed benchmark says little about your tasks. Look the benchmark up there
  before quoting a vendor's number, and let your own cases decide.

## What the first run showed

One run, 2026-09-29: a nightly single-shot call that reads a memory store of about 268k tokens
and reports contradictions, superseded facts and duplicates, graded on the
[planted-defect cases](planted-defect-evals.md), two repetitions per case per setting. Goal:
keep accuracy, cut cost, same model.

- **Most of the cost was a cache the call never read.** The call wrote its whole input to a
  1-hour prompt cache and, running once a night, never read it back. Switching to the 5-minute
  cache cut cost per call by about 28%, measured on one case, and by construction changed
  nothing the model saw or said. Read the
  usage block's cache-write split before touching the prompt.
- **Price every variant as production pays, not as the runner reports.** Two repetitions of
  a case within the cache window read each other's cache, so the runner's figure was lower than
  anything the nightly job would ever pay. Every row was priced as all input written to cache,
  no reads, plus output.
- **Lower effort cut recall and left precision alone.** Caught planted problems fell to 62% at
  low effort and 81% at medium; every setting left all 12 look-alikes alone. A detector that
  stays quiet on look-alikes can still be missing a third of what it should find, so score
  both.
- **The winner was one effort notch down plus one sentence of search instruction** (go
  subject by subject and compare what each file claims about the same mechanism), which
  matched production's recall at about 45% lower cost and about a third of the time. The step
  without the sentence met the minimum by zero, and its repeat fell below it; the step with
  it met the minimum by one, inside noise, so it counted only after a repeat run held. Register
  the minimum before round one, and repeat any winner whose margin is inside noise.
- **The sentence was written after reading the misses, and there was no held-out set,** so
  its gain is partly tuned to these cases.
- **The runner refused a production argv that already carried the flags it injects.** So the
  final flags went into production code after the climb, and the argv production actually
  builds was captured and diffed against the one that was measured. They matched. Without that
  refusal, a flag could be applied twice or measured once and shipped differently.
- **The optimized call had no consumer until someone checked.** The scheduled job that runs it
  had never been enabled (found 2026-09-30), so a cheaper call saved nothing. Check the
  consumer before the climb as well as after.
