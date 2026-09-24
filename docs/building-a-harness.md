# Building your own harness

Written 2026-09-23, when an operator asked whether to replace their coding tool's built-in agent
loop with one of their own. The same brief went to four models from three vendors, each in its own
sandbox with no view of the others: GPT-6 Sol through the codex CLI, Grok 4.7, Claude Opus 5.5 and
Claude Fable 5.1. A second operator priced a week of their own sessions independently. All four
models reached the same verdict. Treat that as a strong default, not a proof: convergent answers
suggest one option dominates, and models can share a blind spot. What follows is what held up when it
was checked against vendor documentation and the two operators' own transcripts.

## The verdict

**Drive the vendor CLIs you already use as short-lived workers, from a thin dispatcher of your own.
Do not start by writing an agent loop against the vendor APIs. Keep your current tool as the
person's way in until its replacement has worked for a week.** This repository is the protocol that
dispatcher speaks, not the runtime.

## Measure first: where the bill goes

Two long-running coordinator sessions on two machines, priced from their own transcripts at API
rates. Both ran on subscriptions, so these are equivalents, not invoices.

| share of cost | sample A (30 hours) | sample B (7 days) |
|---|---|---|
| re-reading context already in the cache | 60% | 70% |
| writing context into the cache | 31% | 18% |
| output | 9% | 12% |
| new input not yet cached | about 0 | about 0 |

Three things follow.

- **Caching already works** in the tool both used. Advice about cache layout gains nothing until you
  assemble requests yourself.
- **Output is the smallest slice.** Telling an agent to write less saves little and costs
  completeness. Never put "save tokens" in a prompt.
- **The bill is window size times calls.** Sample A's main session averaged 530k tokens per call;
  sample B's averaged 533k across 29,000 requests. Every model request re-reads all of it.

Two lines in those samples can be fixed before any new code exists:

- **Workers that inherit the frontier model.** In sample A every one of 2,819 calls made by
  multi-agent workflows ran on the session's frontier model, because a subagent inherits it unless
  a step names one. Name the worker model in every handoff.
- **Cold resumes.** Sample B counted 110 returns in a week after the prompt cache had expired, each
  rewriting about 570k tokens at the cache-write rate: about a tenth of the week's cost. Write the
  handoff before walking away ([`context-steward`](../skills/context-steward/SKILL.md) §7).

**Pricing your own.** Claude Code writes each session as JSON lines; every assistant message carries
a `usage` block with input, output, cache-read and cache-write counts (cache writes split by TTL).
Multiply each by its rate. Two traps: the same message can appear on several lines with a partial
output count, and taking the first line undercounted sample A's workflow output sevenfold, so
dedupe by message id and keep the largest count. And keep the rates in a file with the date you
read them; a rule built on a price has an expiry nobody writes down. For headless runs,
`claude -p --output-format json` returns `total_cost_usd` and a per-model breakdown. Its own
documentation calls both client-side estimates, and a run started with `--continue` or
`--resume` reports the whole conversation's total, so log the difference from the previous run,
not the figure.

## Billing decides the shape

Read from vendor documentation on 2026-09-23. Terms change; re-read before you build on them.

- **Anthropic**, in the Agent SDK overview: "Unless previously approved, Anthropic does not allow
  third party developers to offer claude.ai login or rate limits for their products, including
  agents built on the Claude Agent SDK." Products built on it use API keys, billed per token.
  Claude Code's own `--bare` mode never reads the subscription login, and it also skips
  `CLAUDE.md`, hooks and plugins, so a harness using it must pass instructions explicitly.
- **OpenAI**, in the Codex authentication page: signing in with ChatGPT is "subscription access",
  an API key is "usage-based access" at standard API rates, and: "Use API key authentication for
  programmatic Codex CLI workflows, such as CI/CD jobs."
- **xAI**'s API is usage-billed.

So the cheapest shape, a personal script driving your own signed-in CLIs, is also the least settled
one for unattended work: Anthropic requires API keys for products built on its SDK, and OpenAI
recommends them for programmatic Codex CLI workflows.
Price the API path before you are forced onto it: sample A's rate, run around the clock on per-token
billing, is several thousand dollars a month (one model's estimate: $285 per 30 hours is about
$6,800 over 720 hours).

| option | billed through | when |
|---|---|---|
| your current tool, worker models named, coordinator kept lean | subscription | first: the baseline everything else must beat |
| a thin dispatcher over vendor CLIs in headless mode | each CLI's sign-in: subscription or API key | second, once the first has a measured baseline |
| the Claude Agent SDK | API key | when you have decided to leave the subscription |
| the Codex SDK | whatever the local Codex agent signs in with; check before unattended use | when codex is the main worker |
| an open-source, provider-agnostic harness | your API keys | run [`repo-triage`](../skills/repo-triage/SKILL.md) first; see the routing trap below |
| your own loop against the APIs | per token, every vendor | last: the only option where cache breakpoints, reasoning pass-back and edit formats are yours to tune |

## Build these in from the start

1. **A cost log per call, split by billing type:** which account, which model, input, output, cache
   read, cache write. Without it every later claim of a saving is a guess.
2. **Spend caps the harness enforces,** with the warning going to the person. Never ask the agent to
   economize.
3. **A fixed request order,** once you assemble requests: stable instructions and tool definitions
   first, volatile setup after the cache breakpoint, conversation last.
4. **Tool names in the prompt, full definitions loaded when needed.**
5. **Large outputs to files:** a path, a size and a short tail in the context, never the dump.
6. **Admission by memory, not per-process caps that add up past physical RAM.** Per-service limits
   totaling about 23 GB on a 15.7 GB machine stalled it twice in one day; five parallel agent
   sessions took down a 16 GB machine. Start low (one worker on a 16 GB host), raise the cap only
   from measured peak memory per lane, and make the start past the cap exit non-zero with the
   host and the count.
7. **A setpoint as the unit of dispatch.** No setpoint id, no job: `hsi done` exiting 2 is the
   dispatcher's refusal.
8. **Review rules enforced in code, not prose.** Refuse a reviewer from the author's lane. Produce a
   deterministic list of deleted files, functions and tests before any model reviews, because an
   implementing model is the one least likely to audit what its own change removed. Ask a verifier
   specific claims ("does anything still call the function this diff deletes?"), not "is anything
   wrong?", which one lane answered "no" to while real defects sat in the file. Settle a
   disagreement by reading the source: one three-model review went 2 to 1 the wrong way.
9. **Proof of what each worker loaded.** A worker started in a fresh folder may load no instructions
   at all and say nothing; see the loading notes in [`AGENTS.md`](../AGENTS.md).

## Where this goes wrong

- **More workers lengthen the review queue.** In both setups the limit was the person's review and
  merge time, not agent capacity. Use extra lanes to make each change cheaper to trust, not to make
  more changes.
- **A harness cannot create a habit.** In sample A a written routing plan (one lane implements,
  another reviews) had gone unused for 17 days when a harness was proposed to run it. Run the plan
  by hand for two weeks first. If the log stays empty, that is the finding, and the README's
  fourteen-day rule applies to the harness as much as to this skill.
- **A provider-agnostic loop can erase a routing rule.** If some data may go to only one provider,
  an abstraction that makes providers interchangeable strings removes that rule without a word
  (`repo-triage` step 6).
- **Replacing the phone door first.** Keep the person's current way in until the new one has carried
  real questions and answers for a week.

## What this repository gives a harness, and what it does not

It gives the operator channel (at most three items, ranking rule printed:
[`l0-channel.md`](../skills/hsi-operator/references/l0-channel.md)), the intake contract (a setpoint
and `hsi done`), the honesty labels, and a testing habit (evals that run the real command and must
refuse). It does not give an agent loop, a queue, routing or a state store, and it should not grow
them.

**Proposed, not built:** a `jobs` contract beside `items` and `setpoint` in `hsi --schema` (task id,
setpoint id, owning repo, author lane, model, result path, and a handoff listing what was done,
findings, concerns, deletions and cost), and a review-verdict contract that refuses a reviewer from
the author's lane. The ledger ([#3](https://github.com/rivendale/hsi-operator/issues/3)) and a real
adapter ([#7](https://github.com/rivendale/hsi-operator/issues/7)) are still open.

## Measure, then ratchet

The engineering post [How we made claude.ai 3x faster in two
weeks](https://claude.dev/blog/how-we-made-claude-ai-faster/) (2026-09-23) is front-end work, but
its method transfers: make a number exist, prove it tracks something a person feels before climbing
it, then make CI fail whenever it gets worse. For a harness the numbers are cost per accepted
change, context per call, and time from "worker finished" to "person merged or rejected". What does
not transfer to one person is the scale: a hundred and fifty parallel threads worked because a team
approved every pull request.

## Improving the harness itself

Two papers from September 2026 point the same way, from different directions. Both are lab reports,
not independent replications.

- **Keep a change only if it wins on tasks it was not tuned on.**
  [AIDE-squared](https://arxiv.org/abs/2609.26457) (Weco AI, 2026-09-22) lets a research agent
  propose changes to its own code, benchmarks each version on a task suite, and keeps what performs
  best on hidden evaluations. An 8-day autonomous run found seven successive improvements that held
  up on four held-out benchmarks, one of them out of distribution, and reward hacking fell from 55%
  to 32% without being targeted. The paper also reports the gains carrying over to other base
  models. For your own harness: test a change against tasks, and ideally a model, it was not built
  from before you call it durable.
- **Promote a failure into a rule only when it recurs.** [Ecdysis](https://arxiv.org/abs/2609.11677)
  finds that fixing each individual failure bakes one model's habits into the harness, while fixes
  drawn from failures that recur across distinct tasks generalize better. This repository's
  `AGENTS.md` applies the same test to its own rules.

Both argue for spending effort on the harness rather than chasing the newest model, and for
measuring each change the way [Measure, then ratchet](#measure-then-ratchet) describes.

**Build the stop before you need it.** A worker you cannot stop cleanly is a worker you will
restart by hand. When a dispatcher here was stopped mid-job on 2026-09-24, it wrote the job's
record and ledger line, released its lock, and removed the empty branch and worktree; a timed-out
job kills the worker's whole process group, after a test found a child process outliving its job.

## Honest limitations

Two cost samples from two machines, priced as equivalents, and a panel of models whose agreement is
evidence of a dominant option rather than of correctness. The billing lines are one day's reading of
vendor pages. Where a model's claim could not be checked, it is left out.
