# Testing a detector with planted defects

For any step that reads a store and reports problems in it: contradictions, stale facts,
duplicates, broken references. This is a design from 2026-09-29, written before its first run. The
cases and grading are approved and audited; there are no results yet.

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
- Grade from the saved response, not from the script's printout.
- To capture cost and the served model without editing production code, put a small shim first on
  `PATH` that passes each call through and saves the response. Give it a fake mode that makes no
  model call, and run the plumbing through that first.

[`eval-and-hillclimb.md`](eval-and-hillclimb.md) is the loop these cases feed.
