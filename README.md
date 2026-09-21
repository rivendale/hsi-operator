# hsi-operator

A skill that keeps a human at the strategic level of agent work.

Agents are good at producing things and bad at knowing whether anyone wanted them. This
is the other half: **surface only what genuinely needs a person, and find out what "done"
means before building.**

Two skills. The first has two doors:

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

```
npx skills add rivendale/hsi-operator --skill hsi-operator -g -a claude-code
```

Or read `skills/hsi-operator/SKILL.md` — it is one file and the skill is the prose, not
the code. The CLI ranks items and prints a setpoint back; the judgment is in the prose.

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
- **This does not make anyone use it.** If it goes two weeks unopened, that is the
  finding, and it should be reported rather than answered with more features.

## Prior art and thanks

The `references/` layout and the honesty protocol are adapted from
[ferdinandobons/startup-skill](https://github.com/ferdinandobons/startup-skill) (MIT).
Different domain, same failure mode: an assistant that cheerleads every idea and one that
surfaces everything as important are the same defect wearing different clothes. Their
four-way claim labelling — Data, Estimate, Assumption, Opinion — is a genuine refinement
on the three-way version this started with, because collapsing *estimate* into *assumption*
is what lets a calculation pass as a finding.

Human-systems integration is the other parent. What we took from NASA/DAU/Endsley, what
we refused (seven-domain matrices, learned rankers), and the restricted three-body reading
of L0 live in `skills/hsi-operator/references/hsi-se.md`. Steal patterns; do not vendor them.

## License

MIT.
