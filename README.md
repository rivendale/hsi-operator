# hsi-operator

A skill that keeps a human at the strategic level of agent work.

Agents are good at producing things and bad at knowing whether anyone wanted them. This
is the other half: **surface only what genuinely needs a person, and find out what "done"
means before building.**

Three skills. The first has two doors:

**`hsi-operator`**
- **`how can I help`** — the 3 things that most need you, each as an answerable question
- **`what does done mean`** — acceptance criteria, elicited *before* work starts

**`repo-triage`** — when someone shares a repo, model or tool and asks "is this useful?",
evaluate it against **measured** gaps rather than its own pitch. Most verdicts should be
no. The failure it prevents is adopting on enthusiasm, and its order is deliberate:
licence first because it is the cheapest kill, then maturity, then **does the runtime exist
on the hardware you actually have** — the check most often skipped and the one that kills
most confidently.

```
triage owner/repo            licence, age, activity — the mechanical half
triage --hf org/model        same for a Hugging Face model
```

It answers steps 1 and 2 and says so. Whether the thing is *useful* is judgement, and the
tool does not pretend to have made it.

**`context-steward`** — when a long session nears its context limit, decide what must survive,
write it somewhere durable *before* the window closes, and keep working memory small by moving
detail **out** rather than summarising it **away**. A summary is a pointer, not a substitute: it
drops the file path, the exact error and the number, and it drops them silently. Includes the
gauge rule that prompted it — check the actual context meter, not a token budget, and act at 80%
rather than 95%.

## Why three

A list of twenty-seven is a list of zero. The scarce resource is not willingness, it is
attention in one sitting. So the tool ranks and shows three — and prints the ranking rule
every time, because a hidden ranking is a judgement you cannot audit. The rest is one
keystroke away and never dropped.

## The test for what reaches a person at all

> Does the answer depend on the operator's preference, intent, risk appetite, money,
> relationships, legal exposure, or **taste**?

Yes, it is theirs. No, answer it yourself and say what you answered from. Four kinds
qualify: **DECIDE**, **APPROVE**, **EXECUTE** (only they have the hands), and **TASTE**
— which is where UI and UX belong and where they are most often mis-filed.

An item asking a person for a **fact** is a search somebody skipped.

## Install

All three:

```
npx skills add rivendale/hsi-operator --skill '*' -g -a claude-code
```

Or one of them: `--skill hsi-operator`, `--skill repo-triage`, `--skill context-steward`.

Or read the `SKILL.md` you want and keep the file — each skill is one page of prose, and
the prose is the skill. `bin/hsi` and `bin/triage` are scripts **inside** the skills, not
commands on your PATH: after installing they sit at `~/.claude/skills/<skill>/bin/`.

## The contract

`bin/hsi` consumes plain JSON and knows nothing about your systems:

```
hsi items.json          # top 3, ranking rule stated
hsi items.json --all    # everything, grouped by kind
hsi items.json --why ID # the arithmetic for one item
hsi done setpoint.json  # Door 2 as a file; exit 2 if done has no check
hsi --schema            # the full contract
```

An **adapter** turns your world into that contract. `adapters/jsonl-tasks/` is a worked one
reading a line-delimited task file; copy it and change the reader for your tracker. The skill never changes.

## Honest limitations

- **An adapter over structured data cannot write `why_you` or `options`.** The included
  one emits a generic `why_you` and no options, which is weaker than the SKILL asks for.
  Options are the part an agent or a person adds; the adapter's job is to find candidates,
  not to frame them.
- **The ranking is deliberately simple** — four terms, printed, recomputable by hand. A
  weighting nobody can check is a weighting nobody will trust. It will be wrong sometimes;
  `--why` is how you catch it.
- **`hsi done` checks the shape of a check, not its meaning.** It refuses a done with no
  command, number or person behind it, and a few stock judgments like "looks good". It
  cannot tell a check that proves done from one that does not; a person still reads it.
- **This does not make anyone use it.** If it goes two weeks unopened, that is the finding,
  and it should be reported rather than answered with more features. That is now measured:
  `hsi answered --use FILE` records a real answer, and after fourteen days of silence the
  board is replaced by a single line saying nobody is using this. It cannot make the tool
  useful; it can stop the tool from being quietly useless.

## The working agreement

`AGENTS.md` is how agents work in this repo: scope guard, testing, what a long context costs,
and how to talk to the person. Every harness we measured reads that filename, so there is one
file and no alias — and prove what your own tool loads rather than trusting a release note;
`AGENTS.md` has the measurements.
[`starter/`](starter) is the drop-in version for a new repo: `AGENTS.md`, a `CHANGELOG.md`
that asks for the failure behind each change, a `SETPOINT.md` for what done means, and the
one CI workflow. For a repo that already exists, the order matters more than the files —
[`docs/adopting-an-existing-repo.md`](docs/adopting-an-existing-repo.md) starts from the
three failures you actually had and says when to stop. Building your own agent harness:
[`docs/building-a-harness.md`](docs/building-a-harness.md) has where the bill actually goes,
what billing each shape implies, and what to build in from the start.

Resources for agents and for anyone building a harness: [`docs/tools.md`](docs/tools.md) is
what each of the four coding CLIs did when driven headless, dated, and
[`docs/harness-efficiency.md`](docs/harness-efficiency.md) is a checklist for making a harness
cheaper without making it worse, including the defaults a new project should start with.

## Changes

`CHANGELOG.md`, where every entry names the **failure that caused the change**. What moved
is in the diff already; why it moved is the part that does not survive anywhere else.

## Prior art and thanks

The `references/` layout and the honesty protocol are adapted from
[ferdinandobons/startup-skill](https://github.com/ferdinandobons/startup-skill) (MIT).
Different domain, same failure mode: an assistant that cheerleads every idea and one that
surfaces everything as important are the same defect wearing different clothes. Their
four-way claim labelling — Data, Estimate, Assumption, Opinion — is a genuine refinement
on the three-way version this started with, because collapsing *estimate* into *assumption*
is what lets a calculation pass as a finding.

Door 2's three paths (spike, bounded, architectural), the one-way ratchet between them, and
the rule that an approval covers the stage actually shown are adapted from the brainstorming
skill in [obra/superpowers](https://github.com/obra/superpowers) (MIT). We took the
classifier and the gate; we did not take "when in doubt take the heavier path" as a general
habit, because this skill's bias is a *smaller* done, and we did not install the collection:
its session hook re-injects itself at every startup and every compaction.

`evals/trigger/` checks that each skill's description would actually route the prompts it
claims, and `--selftest` proves the check can still fail. Both run in CI on every pull
request. The idea is from
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT), found via
[Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)
(Apache-2.0); rewritten here rather than vendored.

Human-systems integration is the other parent. What we took from NASA/DAU/Endsley, what
we refused (seven-domain matrices, learned rankers), and the restricted three-body reading
of L0 live in `skills/hsi-operator/references/hsi-se.md`. Steal patterns; do not vendor them.

## License

MIT.
