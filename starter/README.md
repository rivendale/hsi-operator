# starter

Four files to drop into a **new** repo so the agents working in it have rules, a record and
one automated gate from day one. Adopting into a repo that already exists is a different
job with a different order: see [`../docs/adopting-an-existing-repo.md`](../docs/adopting-an-existing-repo.md).

| file | goes to | what it buys |
|---|---|---|
| `AGENTS.md` | repo root | the working agreement: scope guard, testing, context cost, how to talk to the person. Most harnesses read this filename; measured 2026-09-21, one of four read a name of its own, so check yours. |
| `CHANGELOG.md` | repo root | a record whose entries name the failure that caused each change. |
| `.github/workflows/evals.yml` | repo root | the one automated gate, if you take the skills check below. |
| `SETPOINT.md` | repo root, optional | what done means for the work in flight, before it starts. |

```
cp starter/AGENTS.md starter/CHANGELOG.md starter/SETPOINT.md /path/to/your-repo/
cp -r starter/.github /path/to/your-repo/   # only with the line below: the workflow runs it
cp -r evals /path/to/your-repo/             # only if your repo has skills
```

## Then do the part that cannot be copied

1. **Fill every bracket in `AGENTS.md`.** The bracketed parts are ownership, the hard
   lines, and the person's own preferences. A kit cannot know them, and a rule nobody
   filled in is a rule nobody follows.
2. **Delete what does not apply.** Every line in that file earned its place by a failure
   somewhere else. A line your repo has never needed is noise that makes the rest cheaper
   to skip. Deleting is the maintenance, not a compromise.
3. **Keep one instruction file.** `AGENTS.md`, no alias and no second copy. Then prove what
   your own tool loads rather than trusting a release note: some harnesses read a project's
   instructions only in a folder you have told them to trust, and "nothing loaded" prints
   exactly like "there is no file here".
4. **Write the first `CHANGELOG.md` entry the first time something breaks.** An empty
   changelog is honest; a changelog seeded with intentions is not.

## If your repo has skills

The check in [`../evals/trigger/`](../evals/trigger) tests that each skill's *description*
would route the prompts it claims, which is the whole surface a harness sees. Copy that
directory and write your own cases; the workflow above already runs it and its `--selftest`.

**Write the cases from outside the description.** Prompts paraphrased from the description
grade it against itself and pass for that reason — the first version of that check in this
repo did exactly that, and two reviewers had to say so before it was worth running.

## What this kit deliberately does not include

- **A hook, a linter or anything that enforces the prose.** Nothing here is enforced except
  the skills check. A rule is something a person and an agent keep, and pretending
  otherwise moves the argument to the enforcement instead of the rule.
- **A workflow engine, a dashboard, or a second place to write facts down.** Decisions and
  lessons belong wherever your repo already keeps them.
- **Vendor dependencies.** No API key is needed to use any of this.
