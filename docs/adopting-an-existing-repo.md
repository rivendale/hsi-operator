# Adopting this into a repo that already exists

The starter kit assumes an empty repo. A repo with history, habits and people in it is a
different job: the risk is not missing rules, it is **adding sixty lines nobody follows**,
which teaches everyone that the file is decoration.

So adopt in the order below, and **stop when the next step is not paid for by a failure you
can name.** Three rules someone keeps beat thirty nobody reads.

---

## 1. Write down the three failures you actually had

Not best practice. The last three times an agent or a person did the wrong thing in *this*
repo. A refactor that swallowed a one-line fix. A test written after the code that passed
because it described the code. An approval of a plan that was spent as approval of a deploy.

Those three sentences are your `AGENTS.md`. Copy from
[`../starter/AGENTS.md`](../starter/AGENTS.md) only the sections that match them, and
delete the rest. Add a section the day it earns its place.

**How you know it worked:** the next time that failure starts to happen, someone cites the
line. If a month passes and nobody has cited any line, the file is furniture — say so out
loud rather than adding to it.

## 2. Make it one filename, and prove what loads it

`AGENTS.md` at the root, and `CLAUDE.md` as a **symlink** to it. One inode, no drift, both
names resolve, and no chance of two instruction files disagreeing while the auto-loaded one
silently wins.

Then prove it, per tool, in this repo:

- ask the tool what it loaded rather than trusting a release note;
- remember that some harnesses read a project's instructions only inside a folder you have
  told them to trust — and that "nothing loaded" prints exactly like "there is no file
  here";
- a version measured at the start of a session may not be the one that ran.

**How you know it worked:** for each tool your team uses, you can name the file it loaded
and the day you checked.

## 3. Put the record where the work is

A `CHANGELOG.md` whose entries name the failure that caused each change, and one place for
decisions with the date and the reasoning **in the decider's own words**. A verdict without
its reasoning cannot be applied to the next case, which is why the same argument returns.

Do not create a second place for a fact that already has a file path. If the repo already
has an architecture-decision folder, that is the place; point at it and move on.

**How you know it worked:** a question settled six weeks ago gets answered from the file
instead of re-argued.

## 4. Fix the testing habit before adding any test

This is the step most worth the argument:

- **Never write unit tests after the code.** A test written by whoever wrote the
  implementation encodes what the code does, not what it should do, and passes for that
  reason. The ground truth has to come from outside the thing being graded.
- **Prefer end-to-end runs**, and have each leave a **verifiable, repeatable artifact**: an
  exit code, a file, a number someone else can reproduce.
- **Where isolation is unavoidable, write the failure list first**, then build against it.
- **Prove any new check in the denying direction.** Feed it something it must refuse. A
  check nobody has watched fail is a check nobody should trust.

**How you know it worked:** you can point at a check that failed for a real reason and was
not immediately weakened to make it pass again.

## 5. Add the one gate, last

If the repo has skills, take [`../evals/trigger/`](../evals/trigger) and the workflow in
[`../starter/.github/workflows/`](../starter/.github/workflows): the check plus its
`--selftest`, so a green tick means both "the descriptions still route" and "the checker can
still fail".

If the repo has no skills, **do not add a gate for the sake of having one.** An automated
check that tests nothing anyone worried about is a tax with a tick next to it.

---

## What not to do

- **Do not paste all of `AGENTS.md` on day one.** A long file at the start of every session
  costs tokens at every startup and every compaction, and the sections nobody needs are the
  ones that make the rest skippable.
- **Do not install a collection of skills to see what sticks.** Install the one that fits
  the failure you named, and pin it to a reviewed commit rather than tracking a branch: a
  skill is instructions, so tracking a branch lets a future push change how an agent behaves
  with no review on your machine.
- **Do not add enforcement to win an argument about a rule.** If a rule is not kept, a hook
  becomes the thing people route around.
- **Do not let the adoption become the work.** If a month of this has produced no cited line
  and no caught failure, stop and report that. It is a finding, not a reason to add more.
