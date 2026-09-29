# Choosing effort by what a finished task costs

Written 2026-09-29. Vendor guidance is quoted from Anthropic's engineering posts, read that day.
Benchmark figures are other people's; the Bug Hunt figures were re-read from the benchmark's
raw data that day, and the Vals figure is reported, not re-read.

## The rule

Price effort per completed task, not per token or per call. "Two models with the same cost per
token can cost very different amounts on the same task"
([What a task costs on Opus 5.5](https://claude.dev/blog/what-a-task-costs-on-opus-5-5/), Addy
Osmani, 2026-09-25). A cheaper model at a high level can cost more per result than a stronger
model one level lower, and which one wins changes from level to level.

## What the vendor says (read 2026-09-29)

- Effort "gives the model an approximation of how much compute you want it to spend on the
  task." The author's rule of thumb: low for quick answers while you stay in the loop, medium for
  most regular engineering, high "for work where verification is important or there are edge
  cases", and max when "I want Claude to operate fully autonomously to solve difficult problems"
  ([Spending your effort](https://claude.dev/blog/spending-your-effort/), Thariq Shihipar,
  2026-09-25).
- "On Opus 5.5 the default is medium, one level below Opus 5's default of high" (the Opus 5.5
  post above). Sonnet 5.5 defaults to high on the Claude API and medium in Claude Code. For its
  starting point: "Start with high unless your workload is agentic or latency-sensitive." At
  xhigh or max, "Sonnet 5.5 will think longer and cost more... In that case, consider Opus 5.5"
  ([Building with Claude Sonnet 5.5](https://claude.dev/blog/building-with-claude-sonnet-5-5/),
  Addy Osmani, 2026-09-28).
- Levels are recalibrated per model. Moving from Sonnet 5, "your old setting won't carry over"
  (the Sonnet 5.5 post); moving from Opus 5, "don't carry over a level you chose for Opus 5" (the
  Opus 5.5 post). Measure again after any model change.
- **Whether a change of effort keeps the prompt cache depends on where you call from.** In
  Claude Code, "On Opus 5.5 with an API key or a Claude subscription, changing effort keeps the
  cache"; on Amazon Bedrock, Google Cloud's Agent Platform or a Claude apps gateway, "a change of
  effort still clears the cached conversation" (the Opus 5.5 post). Calling the API directly,
  "Changing the top-level effort between requests invalidates the cache; to run one turn at a
  different level, use per-message effort (beta), which keeps the cache" (the Sonnet 5.5 post).
  Raising effort for one hard step is cheap only where the cache survives it.

## What others measured

- **Bug Hunt Bench** ([bughunt.productcompass.pm](https://bughunt.productcompass.pm/)): 105
  planted bugs in two repositories, each model in its own CLI, graded blind. Figures below are
  computed from its raw data (`results/runs.csv` in
  [phuryn/bug-hunt-bench](https://github.com/phuryn/bug-hunt-bench), commit 9f3b417, read
  2026-09-29): total cost at list price divided by total planted bugs fixed, across every live
  run of that setting. The repository has no license file; these are its published results,
  quoted, not reused.

  | effort | Sonnet 5.5, cost per bug | Opus 5.5, cost per bug |
  |---|---|---|
  | low | $0.29 (1 run, 20 bugs) | $0.37 (3 runs, mean 22.3) |
  | medium | $0.47 (1 run, 18 bugs) | $0.52 (3 runs, mean 30.3) |
  | high | $0.52 (1 run, 32 bugs) | $0.70 (3 runs, mean 31.7) |
  | xhigh | $1.19 (3 runs, mean 36.0) | $0.97 (3 runs, mean 36.0) |
  | max | $3.00 (3 runs, mean 51.3) | $1.40 (3 runs, mean 41.7) |

  The model that is cheaper per token was cheaper per result up to high, and more expensive at
  xhigh and max, where it also fixed more. At medium it was cheaper per bug while fixing far
  fewer, which is why a quality bar comes before a price. And one run is not a figure: a screenshot of the same board shared earlier that
  day showed Sonnet 5.5 at xhigh as $1.55 per bug from a single run, and its three max runs range
  from $2.14 to $4.48 per bug.
- **Vals AI**, in a post on X about its MysteryMechanism benchmark (September 2026; figures from
  the post's chart, not re-read here): Opus 5.5 at high and at xhigh both scored about 41%, xhigh
  at about 3.6 times the cost.

Neither is your workload. Both show the shape: price per token does not predict price per result,
and a higher level can buy nothing.

## How to choose

1. Write down the task unit and the quality bar first: a ticket closed, a bug found, a file
   correct.
2. Run the current setting twice, as a noise check.
3. Walk a staircase, not a grid: the model's recommended level, then one step down, then the
   stronger model one level lower. Stop a direction when it falls below the bar. At least three
   trials per setting.
4. Keep the setting that clears the bar at the lowest cost per completed task, and write down what
   the cheaper settings got wrong even when you do not pick them.
5. Pin full model IDs and pass effort explicitly on every scripted call. On 2026-09-29 the alias
   `sonnet` resolved to the older model on one Claude Code version and to the newer one after the
   next update. A scripted call with no effort flag probably inherits its caller's level (an
   assumption, not measured).
6. Check what served the call from the call's own output: `claude -p --output-format json`
   reports `modelUsage`. A long-running session keeps the binary it started with, so check the
   running process, not `claude --version`; a subprocess runs whatever is first on `PATH`.

[`harness-efficiency.md`](harness-efficiency.md) puts reasoning effort in the "write a proposal"
tier. This page is what that proposal should measure.
