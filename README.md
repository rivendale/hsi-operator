# hsi-operator

A skill that keeps a human at the strategic level of agent work.

Agents are good at producing things and bad at knowing whether anyone wanted them. This
is the other half: **surface only what genuinely needs a person, and find out what "done"
means before building.**

Two doors, neither subordinate to the other:

- **`how can I help`** — the 3 things that most need you, each as an answerable question
- **`what does done mean`** — acceptance criteria, elicited *before* work starts

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
the code. The CLI only does the ranking.

## The contract

`bin/hsi` consumes plain JSON and knows nothing about your systems:

```
hsi items.json          # top 3, ranking rule stated
hsi items.json --all    # everything, grouped by kind
hsi items.json --why ID # the arithmetic for one item
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
- **This does not make anyone use it.** If it goes two weeks unopened, that is the
  finding, and it should be reported rather than answered with more features.

## License

MIT.
