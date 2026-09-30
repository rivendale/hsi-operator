# Design rules for code, as rules with checks

An agent that can explain a design principle will still break it when the principle is prose.
The rules below are the few that bind behavior in a code repo, each with the check that makes
it hold. The idea of writing design principles as hard rules in `AGENTS.md`, rather than as a
list of virtues, is Tomas Vykruta's (@tvykruta on X, 2026-09-30); the wording and the checks
here are ours.

They extend what is already here: the scope guard's "what the project already does, then the
standard library" order and "delete what you replaced", in
[`starter/AGENTS.md`](../starter/AGENTS.md#scope-guard), and Testing's "a rule the agent agrees
with and still breaks needs a mechanical check", in [`AGENTS.md`](../AGENTS.md#testing). The compact version
for a new repo is in [`starter/AGENTS.md`](../starter/AGENTS.md#design-rules).

## 1. Reorganize first, then change

When a change needs a reorganization, it goes in two commits: a refactor that preserves behavior, with the tests green,
and then the change. This is not license for unrelated refactoring, which the scope guard
still drops; it applies when the change cannot be made cleanly without moving code first. They
may share one pull request, never one commit. A reviewer has to be able
to verify that the first commit changes nothing, and a mixed diff makes that impossible: the
behavior change hides among the moved lines.

For a high-stakes calculation (money, dosage, tax, anything a person relies on), a green suite is
not enough evidence that nothing moved. Dump the outputs for a fixed set of inputs before the
refactor, dump them again after, and diff the two. An empty diff is the proof; attach the command
to the commit.

## 2. One owner per fact

Each business rule, threshold, price table, model ID, format or schema fact has one owning module.
Everything else calls it. Extend the owner; add a new module only with a stated reason the old one
cannot own the fact.

**A function-level import used to dodge an import cycle means the logic is in the wrong module.**
The cycle is the design telling you two modules both think they own something. Move the logic,
do not hide the import.

This is the code form of a rule already in the starter's record-keeping section: one fact in five
files is five fixes.

## 3. Grep for the expression, not the function name

Before a second use of existing logic, search for the expression itself: the arithmetic, the
format string, the threshold value, the model-name string. A search for the function name finds
the callers of the one copy somebody named; the copies that matter are the ones inlined where
nobody named anything.

List every copy. Then either move them all to the owner, or have the commit message name each copy
left behind and why. **A new helper written beside the old copies is one more duplicate**, and the
most convincing kind, because it looks like the cleanup.

The move preserves each caller's exact results, including the ones that differ from each other.
Two copies that disagree are a finding: record which one is right, and make the behavior change its
own commit (rule 1).

## 4. No business logic in display code

Templates, components, routes and view builders display values. They do not compute prices, totals,
eligibility or classifications. A total computed in a template is a second owner of the pricing
rule (rule 2) that no test of the pricing module ever exercises.

**Who may see a value is decided on the server, not by a conditional in a component.** A hidden
field is still in the payload, and anyone who opens the network tab reads it.

## 5. When two principles conflict, pick the lowest future cost

Principles collide: a shared helper against a local copy, a general interface against the one call
site that exists. Choose whichever leaves this repo cheapest to change next, and say in the commit
message which principle lost and why. The written reason is what lets a later reader tell a
decision from an accident, and it is the only part of the choice anyone can review.

## 6. Gates, not promises

A rule that matters ships with a check (a lint rule, a test, a hook) that fails when the rule is
broken. **Add a rule with its check, or label it review-only**, and prove the check in the denying direction:
feed it a violation and watch it fail before trusting it green.

Worked examples, each small enough to write in an afternoon:

- **Model names live in one file.** A lint rule, or a test that greps the source tree, refuses any
  model-ID string outside the one model-config module. Prove it by adding a model string to a
  scratch file and watching CI fail.
- **Every model in use has a price.** A test enumerates the models the config can select and fails
  if any has no entry in the price table. Prove it by adding a model to the config without a price.
- **No parent without its child.** A test drives every code path that creates a parent record (an
  order, an account, an invoice) and fails if the required child record (its line items, its
  owner, its ledger entry) was not created with it. Prove it by deleting the child write on one
  path.
- **Display code cannot import the rule owners.** An import-boundary lint (import-linter in Python,
  `no-restricted-imports` in ESLint) refuses a template or component that imports the pricing or
  permissions modules. This only partly gates rule 4: it misses arithmetic written inline in a
  template, which imports nothing, and it says nothing about visibility.
- **A restricted field never reaches an unprivileged role.** A test requests the page or endpoint
  as each unprivileged role and fails if the response payload contains the restricted field at
  all, hidden or not. This gates the server-side half of rule 4. Prove it by moving the check back
  into the component, so the field ships and the component hides it.

Rules 1, 3 and 5 are review-only, and rule 4 is partly gated: a checker cannot tell a refactor
from a change, find every inline copy of a rule, or know a principle lost. Label them so in the
file rather than implying a gate exists. For rule 1 the output
diff is the check; for rule 3 the list of copies in the commit message is the evidence a reviewer
reads.

## What to leave out

- **Generic principle lists** (SOLID, the Law of Demeter, DRY stated on its own). They lengthen the
  instruction file without binding any behavior, and every line of prose makes the binding lines
  cheaper to skip. Keep a principle only in the form of a rule a reviewer or a check can apply.
- **Self-reported before-and-after numbers.** "Duplication down 40% after adding these rules",
  measured by the same agent that followed them, is not evidence. The process is the lesson: the
  refactor commit, the grep, the check that failed before it passed.
