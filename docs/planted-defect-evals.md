# Testing a detector with planted defects

For any step that reads a store and reports problems in it: contradictions, stale facts,
duplicates, broken references. This is a design from 2026-09-29, written before its first run;
what the first run showed is in [`eval-and-hillclimb.md`](eval-and-hillclimb.md).

1. **Freeze the corpus.** Record the commit of the store and a hash of the code under test. Build
   each case in a scratch directory from that commit, never from the live store.
2. **Plant one defect per case, each against one real item:** a contradiction (same subject, same
   date, opposite claim), a superseded fact (a clear order in time), a duplicate (same incident,
   nothing added).
3. **Add look-alike negatives:** a new item on the same subject that is compatible with its
   neighbor, such as a refinement or a second fact about the same mechanism. They measure
   specificity, which recall alone hides.
4. **Add unmodified controls.** Findings on a control are the baseline: problems already in the
   real store. Read extra findings against it, because some of them are real.
   **A control can hold a real defect its author missed.** When every run of every variant flags
   the same thing on a control, re-read the control before blaming the reviewer. In one public
   set ([rivendale/ai-redteam](https://github.com/rivendale/ai-redteam)), a "clean" request said the audit record must say who acted, and its patch made the actor
   optional. Every reviewer was right.
5. **Grade in code.** Detected: some finding names the planted item and its target. Kind right:
   the finding's kind is one the case accepts. Look-alike pass: no finding names the planted item.
   Normalize names before matching.
6. **Have a second agent audit the cases before anything runs.** In our set of 24 (6
   contradictions, 5 superseded, 5 duplicates, 6 look-alikes, 2 controls), an audit against the
   frozen store fixed five: an implausible version number, wording that read as a value already
   applied, a look-alike that restated its target closely enough to count as a duplicate, one
   ambiguous phrase and one unmeasured claim.
7. **Report difficulty honestly.** A case whose wording uses the detector's own cue words
   ("supersedes", "corrected on") is easier; report it apart from its harder twin. Measure a trivial
   baseline too: word overlap alone scored 0.78 balanced accuracy on our duplicates, so a detector
   has to beat that to be worth running.
8. **Label every planted file as false** in a README beside them, and never glob the fixture
   folder; copy in only the file a case names. If an agent can search that folder as notes or
   memory, a planted falsehood can come back as a fact.

## Where the runner goes wrong

- A cache or state store that skips inputs it has seen makes a repeat trial exit 0 with no model
  call, and trials can write planted findings into production state. Isolate the state and force a
  fresh run.
- If the model under test has tools, it can open the answer key. Turn tools off, and confirm one
  call still returns structured output.
- Session hooks fire in every eval call unless you disable them.
- **Make a scratch copy with `git worktree add` or `git clone`, never `cp -r`.** A linked
  worktree's `.git` is a one-line file pointing at the original worktree's metadata. A `cp -r`
  copy keeps that pointer, so `git add` in the copy changes the original worktree's index.
  Reproduced 2026-10-07: `git add` in the copy showed up in the original's `git status`.
  Check: `git rev-parse --git-dir` must print different paths in the copy and the original.
- Grade from the saved response, not from the script's printout.
- To capture cost and the served model without editing production code, put a small shim first on
  `PATH` that passes each call through and saves the response. Give it a fake mode that makes no
  model call, and run the plumbing through that first.

## Where the grader goes wrong

- **A checker that cannot pass is as worthless as one that cannot fail,** and more likely to be
  believed, because a red check reads as diligence. Write discrimination tests: assert which
  verdict each scenario produces, not that the check ran. One backup checker reported "no host
  holds an identical copy" when another host held identical copies of two of three samples; two
  conditions had collapsed into one word. It needed three: copies disagree (reconcile), no copy
  exists (exposed), and no comparable sample (unknown, a failure to measure, which prints as
  neither pass nor absence). Then add a meta-test that fails the suite if fewer than the
  expected number of distinct verdicts are reachable, or if the passing verdict never is.
- **A mutation the check survives is a finding, not noise.** Weaken the check in several
  different ways, not one. A scorer's self-check failed correctly when the rule "a High finding
  on a clean case counts as a false alarm" was deleted. It still passed when the severity table
  ranked High equal to Medium, because no fixture told the two apart. The fix was a fixture, not
  a reworded rule. Put the result in the pull request as a table, one row per mutation:

  | mutation | step that should fail | exit code |
  |---|---|---|
  | delete the High-is-a-false-alarm rule | scorer self-check | 1 (caught) |
  | rank High equal to Medium | scorer self-check | 0 (survived: add a fixture) |

  A row with exit 0 is open work, and the table shows a reviewer which faults were tried.
- **Score in the same checkout the reviewers saw.** One coverage metric counted stray
  `__pycache__/*.pyc` files that existed only in the scorer's checkout. They inflated "coverage
  omits a file" violations by about a third. Score from a clean clone, or skip files git
  ignores (`git ls-files` lists only tracked ones), and diff the scorer's file list against the
  reviewer's before trusting a count.
- **Run the old code against the new test.** A sampling bug that could never reach files
  sorting after one letter was fixed with a test asserting "fewer than 20 of 26 directories
  touched". The buggy code touched 22, so the test would have passed the bug. Keep the broken
  version long enough to fail the new test once.
- **A detector over prose scores the warning as the offence.** One harness matched
  anti-pattern strings anywhere in an answer, so an answer that named a trap in order to avoid
  it failed exactly like one that fell in: five of six probes in one run were failed on text
  rejecting the anti-pattern. The failure is directional. The treatment being tested is what
  made answers explain their traps, so the better it worked, the worse it scored. Scoping the
  match to code blocks would not have helped, since both answers were in code blocks. Add a
  fixture that is correct and discursive, one that names the bad thing to reject it, and
  require the detector not to fire on it. When the third fix to a grader lands somewhere new,
  question the grader's shape rather than fixing it again.

## Before a rewrite or port: record the old program, replay it on the new one

**The old program's real behavior is the specification; record it before touching it.** Capture
real invocations and their outputs from the current version, replay every one against the
rewrite, and review each difference as either a bug or an intentional change written down with
its reason. [pbakaus/impeccable#714](https://github.com/pbakaus/impeccable/pull/714) (merged
2026-09-04) replaced a Node runtime with a Rust binary this way: an oracle suite replays 830
recorded command invocations and 16,058 recorded function-call vectors, compared byte for byte,
and the accepted differences are listed in `tests/oracle/DELTAS.md`. A test suite written for
the rewrite tests what its author thought the program did; the recording tests what it did.
Check: the replay runs in CI, the delta file is the only way a difference passes, and a new
entry in it is reviewed like code.

[`eval-and-hillclimb.md`](eval-and-hillclimb.md) is the loop these cases feed.
