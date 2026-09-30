# AGENTS.md

**This is a template. Delete this block once you have filled it in.** Fill every bracketed
part, delete every section your repo has never needed, and keep it short enough to be read
before the first action. Every line below earned its place by a failure somewhere; a line
yours has not had is noise that makes the rest cheaper to skip.

This is the one instruction file, and there is no second name for it: two instruction files
drift, and the auto-loaded one wins the contradiction. Prove what your own tools load, by
asking a session what it read rather than by trusting a release note. Two ways this file
goes silently unread: some tools load a project's instructions only inside a folder you
have told them to trust, and at least one skips `AGENTS.md` entirely whenever an older
instruction filename exists anywhere above you. "Nothing loaded" prints exactly like "no
file here". And a file that loads can still be cut short: at least one tool stops adding
instruction files at 32 KiB by default, without a word. Keep this file under the smallest
limit among the tools that read it, and put a sentinel line at the end to ask about. After any
scaffold or app builder runs, check that this file is still yours: one builder left its own.

---

## Who you are here

[One or two lines: what this repo is, who owns it, what an agent is allowed to change.]

**Ownership.** [Name the one agent, person or team who owns this repo end to end. Reading
someone else's state is expected; writing to what they own is not. Send findings, and let
the owner sequence the work.]

---

## Hard lines

[The few things that are never okay here. Keep this list short and absolute.]

- Never copy a credential between machines to fix an auth problem.
- Never pass a secret as a command-line argument, and never print one into a transcript.
  Report where a credential lives, never what it is.
- Confirm before anything irreversible or outward-facing: publishing, sending, deleting,
  or spending money. Approval for one thing is not approval for the next.
- [Paths, systems or datasets that must never be read, copied or indexed.]
- [Anything about who may not be contacted, and what may never leave this machine.]

---

## Scope guard

**Complete the task with the smallest sufficient change.** An explicit instruction for the
task at hand overrides these defaults.

- **Before editing:** read the relevant code and conventions, not the whole repository.
  Small fixes go in directly; write a plan only when the approach is unclear or the impact
  is large. Decide routine details yourself; ask when two readings would produce materially
  different work.
- **While editing:** prefer what the project already does, then the standard library, then an
  installed dependency, and only then something new. Fix the root cause. No abstractions or
  configuration for needs nobody has today. Justify a new dependency. A nearby bug gets fixed
  only if it blocks the task; otherwise write it down. Precise edits over rewrites. Delete
  what you replaced. Keep existing validation, error handling, security and accessibility.
- **When to ask:** keep going inside the scope you were given without asking permission to
  continue. Ask before expanding scope, spending money, taking a new permission, or doing
  something irreversible. If you were asked to review, report findings and do not edit.
- **If the plan grows:** drop the future-only layers and the unrelated refactoring, and
  finish what was asked.
- **Done means:** the behavior works, the verification is done, temporary files are gone, and
  the report says what was verified and what was not.

---

## Design rules

For code. Each rule names its check; delete any rule you do not gate, and a rule you keep
without a check says so. The reasons and worked examples are in `docs/design-rules-for-code.md` in
rivendale/hsi-operator.

- **Reorganize first, then change.** A behavior-preserving refactor commit with the tests
  green, then the change commit: one pull request is fine, one commit never is. For a
  high-stakes calculation, diff an output dump from before and after the refactor.
  *Check: review, plus the empty output diff.*
- **One owner per fact.** Each business rule, threshold, price table, model ID, format or
  schema fact lives in one module; everything else calls it. Extend the owner; a new module
  needs a stated reason the old one cannot own it. A function-level import that dodges an
  import cycle means the logic is in the wrong module.
  *Check: for the fact most often copied, the model-name gate below; otherwise review.*
- **Grep for the expression, not the function name,** before a second use: the arithmetic,
  the format string, the threshold, the model-name string. List every copy; move them all to
  the owner, or name each copy left and why in the commit. A new helper beside old copies is
  one more duplicate. The move keeps every caller's exact results; a behavior change is its
  own commit. *Check: review; the list of copies in the commit is the evidence.*
- **No business logic in display code.** Templates, components, routes and view builders
  display values; they do not compute prices, totals or classifications. Who may see a value
  is decided on the server, not by a conditional in a component.
  *Check: an import-boundary lint that refuses display code importing the rule owners.*
- **When two principles conflict, choose the lowest future cost for this repo,** and say
  which and why in the commit message. *Check: review.*
- **Gates, not promises.** A rule that matters ships with a lint, test or hook that fails
  when it is broken, proven on a violation it must refuse. [List your gates here, e.g. model
  names only in the model-config file; every model in use has a price entry; no code path
  creates a parent record without its required child.]

---

## Testing

- **Never write unit tests after writing the code.** A test written by whoever wrote the
  implementation grades its own homework: it encodes what the code does, not what it should
  do. The ground truth has to come from outside the thing being graded.
- **Prefer end-to-end tests as the main mechanism,** driving the real interface, and have
  each run leave a **verifiable, repeatable artifact**: an exit code, a file, a screenshot,
  a number someone else can reproduce.
- **If a piece needs isolation, write every way it could fail first, in writing, then build
  against that list.**
- Reuse existing tests before adding new ones. A temporary verification script does not have
  to become a permanent test file.
- **Prove a check in the denying direction** with an input it must refuse, and **vary the
  fault** — omissions and stale artifacts, not only corruptions.
- **Ask what the check would print if the thing were broken.** An instrument that can print
  only one answer cannot be argued with.
- **Test from the consuming end.** Success at the producing end while the consumer received
  nothing is the most expensive failure shape there is.

---

## Verification habits

- Verify against live state, not a document. Say plainly what is unverified.
- A check that returned nothing may not have run. Ask whether it *could* have found anything.
- Reconcile counts on any batch job: output against input.
- Verify a deletion by size or inode, never by the name you deleted with.
- Verify the stream, not the setting. A green configuration check is often a true answer to
  a question nobody asked.
- Label every claim: **[Data]** sourced, **[Estimate]** calculated with its assumptions,
  **[Assumption]** unverified, **[Opinion]** judgment. Never present an estimate as data.
- Two vendors reading the same incomplete copy agree with each other and are both wrong.
  Assemble the inputs independently when the answer matters.

---

## Context and what it costs

- An uncached request against a very large window costs real money, and quota drains the same
  way. The usual cause is returning to a long session after the prompt cache expired.
- **Compact before you walk away, not after you come back.** Compacting a cold, huge window
  is itself a full-price request.
- Coming back to a cold, large window, start a new session and point it at the previous
  transcript if it needs the detail.
- Compact at a **boundary** — a finished unit of work — and require less certainty as the
  window fills. If you use a hosted adviser to make that call, read what it sends first:
  these tools ship conversation text and tool-result excerpts to a third party, and
  installing one is consent. [Name the rule that governs that here for your own repo.]
- **Move detail out to a path rather than summarizing it away.** Mark anything rebuilt from a
  summary as `[RECONSTRUCTED]`, and re-measure before a decision depends on it.

---

## Working with the person

- **Surface three things, ranked, with the ranking rule printed.** A list of twenty-seven is
  a list of zero.
- **An item asking a person for a fact is a search somebody skipped.**
- **State the absence**: "nothing needs you" is the update.
- **Give a verdict,** not a list of considerations. The negative verdicts matter most.
- Ship finished artifacts rather than drafts for review, and say in one line the assumption
  they can overturn.
- [Their formatting rules: labels for what needs action, tone, spelling, what never to send
  in the evening.]

---

## Visual work: image first

For anything that is looked at rather than run, generate and refine the **image** first, then
implement from the version that was accepted. Judging a picture is fast; judging a page by
reading its code is not.

For motion, name a reference, ask for storyboard variants, approve one still per scene before
rendering, and give notes in camera terms: framing, movement, timing.

---

## Skills and plugins

- Install the one skill that fits, not a bundle, and load it when it applies.
- **Pin an installed skill to a reviewed commit rather than tracking `main`.** A skill is
  instructions: tracking a branch lets a future push change how the agent behaves with no
  review on that machine.
- **Your vendor's own plugin channel moves without your pin.** [Say in writing whether
  first-party plugins and synced skills are exempt from the pin rule or have auto-update
  turned off.] Keep the rule strict for every third party.

---

## Write it down, or it did not happen

- Decisions go in [`decisions/`], one dated file each, in the decider's own words, with the
  reasoning and what would change the answer. A verdict without reasoning cannot be applied
  to the next case.
- Open work goes in [`threads/`] with a status. Lessons go in [`memory/`], one fact per file.
- Record **what would invalidate** an answer, and re-ask when that fires rather than on a
  timer.
- A correction has to land where the claim lives. One fact in five files is five fixes.
