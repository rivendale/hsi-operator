# Making an agent harness cheaper without making it worse

A checklist, written 2026-09-24. It draws on the prompt Cursor shared with its article
["Improved token efficiency for longer agent runs"](https://cursor.com/blog/improved-token-efficiency)
(Jediah Katz, Connor O'Keefe and Calvin Yee, Cursor, 2026-09-23). The ideas and the figures
marked Cursor's are theirs; this page is a condensed rewrite, and where a section follows their
structure it says so. Their central rule, in their words: "Change what the harness sends, not
how hard the model tries."

## Whose figures are these

Keep the two sources apart. Neither is a target.

| figure | whose | what it measured |
|---|---|---|
| about 7% lower overall token cost, no quality loss | Cursor, in the article | one round of changes (prompt trimming, tool offloading, cache layout, sparse line numbers, subagent tuning) on their production coding agent |
| 60% fewer tool-description tokens; 46.9% fewer total tokens | Cursor, in the article | moving tools out of static context; the second figure only in sessions that used integration tools |
| workers used at least 69% of tokens; a frontier planner with cheap workers at about one-eighth the cost | Cursor, in the prompt only | large multi-agent runs; not in the article |
| 60% and 70% of cost was re-reading cached context | this repo, [`building-a-harness.md`](building-a-harness.md) | two long coordinator sessions priced from their transcripts, API-rate equivalents (2026-09-23) |
| 2,819 of 2,819 calls made by multi-agent workflows on the frontier model | this repo, same page, sample A | no step named a worker model |

The samples differ in kind, not only in size: Cursor's changes touched what a harness sends,
while both of ours show the bill was mostly the window resent on every call. A large percentage
applies only to the slice a change touched.

## 1. Measure first

- **Count a finished task as the unit.** A per-request saving can be wiped out if the agent
  needs more turns afterwards. Cursor makes the same point.
- **By billing type.** Output, uncached input, cache reads and cache writes are priced very
  differently. Log all four per call, with the model and the account.
- **Then rank** by share of spend, times the fraction you could remove, divided by the risk to
  quality. Read a few rendered requests, not only the templates: duplicates and leaked
  volatile values show up only there.
- Record per tool how many runs call it at all, and its error rate.

If the harness does not log usage by billing type, that is the first change. Everything else
depends on it.

## 2. The layers

**System prompt.** Label each line keep, rewrite, delete or move. Keep what the model cannot
know (the product, the environment) and fixes for quirks you saw in transcripts. Replace
commands and emphasis with plain descriptions. Delete guards against habits you have not seen
from this model. Move anything per-user or per-request after the cache boundary.

**Tools.** Definitions ride on every request. Keep the few tools most turns need in static
context; leave a name and a pointer for the rest, with the full definition available on
demand. Do not offload a tool the model needs on turn one or tries to call when it is absent.

**Cache layout.** Tool definitions, then system instructions, then a breakpoint, then a setup
message with volatile facts, then the conversation. Keep the prefix byte-identical: fixed tool
order, fixed serialization, timestamps and ids after the boundary. Switching models
mid-conversation discards the cache; run the other model as a subagent instead.

**Tool results.** Write large outputs to a file and return the path, the size and a short tail.
Truncating loses data; inlining bloats every later request. Look for overhead repeated per
line (line numbers, absolute paths, ANSI codes, progress bars). Classify tool errors and treat
unknown ones as harness bugs.

**Long runs and subagents.** Keep a compaction prompt short and save the full history to a
file the agent can search. Rewrite running notes instead of appending. Subagents keep the
parent lean but add coordination cost; have each return a short handoff of what was done,
findings, concerns and deviations. Pass reasoning items back on later turns if the API
returns them. Measure the whole tree of agents, not the parent alone.

**Fitting each model.** Use the edit format the model was trained on, name tools after their
shell equivalents for shell-first models, and strip capitals and emphasis for literal ones.
Tie every added instruction to a transcript behavior it fixes, and re-audit when models change.

**Validation.** Replay the same realistic tasks on the old and new harness and diff success,
cost per task and turns. With real users, split traffic and let cost per completed task decide,
watching success and latency so a saving does not hide a regression. Keep the result either way.

## 3. How much to trust a change

Cursor sorts changes into three tiers by how much judgment they need. The tiers are theirs;
the table and the reasons are ours.

| tier | what goes in it | why |
|---|---|---|
| Just do it, one commit per change | Logging of usage and cache hits; anything that only makes the prefix more stable or removes waste with no behavior change (tool order, serialization, breakpoints, files for large outputs); restoring reasoning items that were being dropped | The model sees the same information, so a revert is cheap and quality risk is near zero |
| Ship behind a flag | Prompt rewrites, tool offloading, new output formats, compaction and subagent prompting | The model sees different information, so it needs an A/B run before it becomes the default |
| Write a proposal | Model choice, routing, reasoning effort, how work is split across agents | These are product decisions with a quality and price trade the owner should make |

## 4. Traps

- Telling the model to use fewer tokens or do less. Cursor reports a model that grew reluctant
  to take on ambitious tasks after such a line.
- Truncating tool output instead of moving it to a file.
- Throwing away returned reasoning to trim input: the model then spends tokens rebuilding its plan.
- Anything that differs from one request to the next placed ahead of the cache breakpoint, including a tool list whose order is not fixed.
- Making a model answer in a shorter format than it was trained to use; less output can mean less thinking.
- Counting raw tokens instead of cost, requests instead of tasks, or evals instead of real use.
- Switching models mid-conversation to save money.
- Advice aimed at the small slices. In both of this repo's samples, output was 9 to 12% of
  cost; the window resent per call was most of the rest.

## Start a new project optimized

Defaults for an agent project on day one, before there is anything to measure:

1. **A cost log by billing type** for every call: account, model, input, output, cache read,
   cache write.
2. **A stable cached prefix,** with volatile setup after the breakpoint.
3. **Tool names in context, definitions on demand** for everything outside the core set.
4. **Large outputs to files,** with a path, a size and a short tail in context.
5. **Short handoffs from subagents:** done, findings, concerns, deletions.
6. **No "save tokens" instructions** anywhere in a prompt. Enforce spend caps in code and send
   the warning to the person.
7. **A named model for every worker.** A subagent inherits the session's frontier model
   unless a step says otherwise.

## Limits of this page

Cursor's figures come from one team's product and are not ours to verify. This repo's two
samples are equivalents priced at API rates from two machines. Neither says what your harness
will save; the measure-first step does.
