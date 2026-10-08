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

**Long context changes the ranking.** Read from vendor pages on 2026-09-24:

| | standard rate (per Mtok, in / cached / out) | above a long-context threshold |
|---|---|---|
| Claude Opus 5.5 | $4 / $0.20 / $20 | none: Anthropic's pricing docs say Claude 4.6 and later models "include the full 1M token context window at standard pricing" |
| GPT-6 Sol | $2 / $0.20 / $10 | $4 / $0.40 / $15 in OpenAI's long-context tier (read 2026-09-22) |
| Grok 4.7 | $2 / $0.50 / $6 | $4 / $1.00 / $12 at or above 200k tokens (xAI docs) |

A coordinator that carries a 500k-token window on every call (sample A above averaged 530k) sits
past both surcharge thresholds on every request, so the vendor that looks cheapest per token for a
short job can cost the most for this one. Route long-context coordination and short worker jobs by
their own economics: the short jobs are where the cheaper models compete.

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
   ([`writing-a-brief.md`](writing-a-brief.md) has the rest of a delegate's brief.)
   - **A model that ranks does not grade its own ranking.** Any check of a ranking, a score or a
     summary runs on a different model, or in code. Models differ widely in how often they take a
     planted shortcut. The Center for AI Safety's [CheatBench](https://www.cheatbench.ai/)
     reports cheat rates from 11.2% to 78.0% across nine models in its setup. That is as
     reported; we have not reproduced it. A self-check inherits whichever rate its model has.
   - **Reviewers get no edit or write tools.** A reviewer that can edit becomes an implementer the
     first time a fix looks easy. Remove the tools; do not rely on asking.
   - **A fix that would grow the change goes to a person, and fixes prefer simplifying.**
     [kunchenguid/no-mistakes#892](https://github.com/kunchenguid/no-mistakes/pull/892) (MIT; merged
     2026-08-29) changed only prompt wording, with tests and docs to match, in an AI review loop
     whose fix rounds kept "growing into machinery nobody scoped": a finding whose smallest honest
     remedy would extend the change beyond its stated intent goes to the user, because the remedy,
     not the defect, needs authorization; fixers prefer "addressing a deeper architectural reason
     and simplifying it, than introducing machinery to handle the symptoms"; and when defects sit in
     code an earlier fix round added beyond what its finding required, the rereview recommends
     reverting to the minimal fix.
   - **When every round finds a new class of defect, change the design, not the patch.** The
     [opensource repository's lessons](https://github.com/rivendale/opensource/blob/main/lessons/README.md)
     ("Building with AI agents in the loop", item 4) have the case.
   - **A verifier works from a fresh clone and writes its own list of ways the change could fail
     before checking anything.** Keep only the findings the verifier confirms or downgrades.
   - **Never judge a gate by text the reviewed change can influence.** In one CI setup, a pull
     request that edited the review workflow made the reviewer print the error patterns, and the
     gate flagged itself; the fix was to judge only the exit code and empty output. For an AI
     reviewer, the diff it reads is input an attacker can write.
9. **Proof of what each worker loaded.** A worker started in a fresh folder may load no instructions
   at all and say nothing; see the loading notes in [`AGENTS.md`](../AGENTS.md).
10. **Hand files over atomically.** When one agent leaves a file for another, write it under a
    temporary name in the same directory and rename it into place, and refuse to copy across
    mounts: a reader can otherwise pick up a half-written file. This is for handoff folders.
    Writing to a path a user names is different, because a rename changes what a plain write does
    to `/dev/null`, a FIFO or a file's group (see this repository's
    [`CHANGELOG.md`](../CHANGELOG.md)).
11. **Hooks allow or deny; they never ask.** An `ask` outranks an unattended mode, so one hook
    that asks turns a workflow that runs alone into one that waits for a tap. On one host, 627
    of 1,224 logged hook decisions were asks, and most of one day's came from a single rule
    firing on a routine `git pull`. Turn an ask into allow at the one function every rule
    returns through, not at each call site, so rules added later are covered. Keep logging the
    original decision, so "which rules would have asked" stays a query. Fewer prompts is not
    weaker denies: the same fix broadened a force-push rule to catch the flag wherever it sits.
12. **Scope is what the tools allow, not what the prompt says.** A subagent in a workflow
    described as "read-only on the filesystem" opened a tunnel to a production database;
    nothing was queried, and nothing in its tools had stopped it. A capability the agent can
    invoke is in scope whatever its instructions say, and a fan-out multiplies one unenforced
    sentence into many chances. Deny the capability, and better, give a survey agent no
    credential for the thing at all: a command-pattern deny has spellings around it, an absent
    credential does not. The same holds for a shared working directory: several agents told
    to play blind read each other's private briefs from the folder they shared, so give each
    participant its own directory and check for leaks every round. And for a sweep over mixed
    stores, a prompt that said in capitals never to open credential-shaped files still had
    agents print logins into their transcripts; the rule held only where the enumerator never
    listed the path. Hand agents a path list built by code. The inverse is also true: a
    parent's memory does not reach a subagent, so the prompt is too weak to enforce a scope
    and still the only place a warning can be delivered. Put the warning in the prompt
    **and** deny the capability. When auditing what an agent did, extract the commands it
    executed; a transcript full of `SELECT` strings may hold only the agent describing a plan.
13. **Let an agent batch actions, but stop the batch on any state it did not predict.** A
    harness that sends one action per model call pays a full request per keystroke; one that
    sends a whole plan blind walks into whatever changed on step two. The middle is checked
    batching. The harness in [An LLM Beat NetHack](https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/)
    (2026-09-21) read position, health, turn, level and nearby creatures before each step, sent
    one step, compared the result with what that step should have produced, and halted the rest
    on low health, a nearby creature, an unknown destination, unexpected displacement, damage, a
    level change or too many turns passing. Fights got no batching at all. For a coding agent
    the same shape is a sequence of commands that stops when an exit code, a changed file count
    or a dirty tree differs from what the plan assumed. Check it by running a batch against a
    fixture where step two fails, and confirm step three never ran.
14. **No third-party router or reseller between the agent and its provider.** Every hop sees the
    prompts, the tool results and the credentials in plaintext, and it writes the response the
    agent acts on, so it can add tool calls the model never made.
    [Your Agent Is Mine](https://arxiv.org/abs/2604.08407) (arXiv 2604.08407, 2026) tested 428
    routers, 28 paid and 400 free: 9 (one paid) injected malicious code into responses, and 17
    touched canary cloud credentials the researchers had planted. Talk to the provider's own
    endpoint, or to a gateway you run yourself. To check, list the NAMES of every base-URL override
    and proxy the agent could inherit, never their values, since a proxy URL can carry a password:
    `env | grep -ioE '^[^=]*(base_url|api_base|endpoint|proxy)[^=]*'` in the environment the
    unattended job actually runs in. For the CLIs' config files and any `.env` beside them, list
    the matching files with `grep -ilE 'base_url|api_base|endpoint|proxy'`, then read only the
    hostname from each hit. Each hit is either the provider's domain or a decision someone can
    name.
15. **Read `.claude/`, `.cursor/` and `.vscode/` in a cloned repo before opening it with an
    agent.** Project settings in those folders can define hooks, tasks and MCP servers that run
    commands when the tool opens the workspace, so opening the repo is running it. Google Threat
    Intelligence Group's [From prompting to autonomy](https://cloud.google.com/blog/topics/threat-intelligence/from-prompting-to-autonomy-the-evolution-of-adversarial-ai)
    (2026-09-08) describes a credential stealer that drops files into exactly those folders so
    that it "executes automatically whenever the IDE or AI extension opens the workspace". It
    also describes two separate supply-chain routes: trojanized forks of MCP servers published
    from compromised developer accounts, and compromised versions of other packages published
    with valid signed build attestations, which pass a provenance check. So provenance is not
    review. Before the first agent session in a fresh
    clone, `git ls-files .claude .cursor .vscode .mcp.json` and read every file it lists, and
    re-read after any pull that touches them.

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
- **A message queued for the next session start never reaches a session that never restarts.**
  In one setup this happened three times in a month; once, instructions to an always-on agent sat
  undelivered for four days while the coordinator told the person the agent was working on them.
  If a message changes what another agent does in the next hour, send it over a live channel; a
  durable record goes to the queue; anything load-bearing goes to both. Before telling the person
  an agent is on it, check that the agent was told.
- **A guard added after a long-lived session started does not protect it.** Hooks are read at
  session start. A hook that blocks a known hazardous command landed about a day after an
  always-on service session had started; the service session ran that exact command the next
  day and froze its host, while a fresh session was blocked by the same guard on its first
  try. Every guard is tested from a session newer than itself, so the one session that can be
  older than its protections is the one that runs unattended. Adding or changing a hook is not
  done until the long-lived session has restarted; compare the hook file's time with that
  session's start time.
- **An auth check that reads the status code can pass forever.** One MCP server rejected a
  wrong or missing key with HTTP 200 and the refusal in the JSON-RPC body (`isError: true`,
  "unauthorized"), so `curl -w '%{http_code}'` reads 200 whether the key is valid, wrong or
  absent. And the operations differ: `tools/list` answered in full with no key, because the
  handshake is open by design, while `tools/call` was gated. Test the gated operation three
  times (real key, wrong key, no key) and assert on the body. The wrong-key arm matters most,
  since no key at all can fail for reasons unrelated to the gate.
- **A memory that writes its own rules will teach itself contradictions.** An agent that
  distills lessons into a store it later loads as instructions keeps adding, and nothing it adds
  is checked against what is already there. On one setup, the first run of a nightly
  contradiction check over such a store found five contradictions or duplicates. Give a
  self-updating store a detector that runs on a schedule, and test the detector with planted
  cases ([`planted-defect-evals.md`](planted-defect-evals.md)) before trusting its silence.
- **Per-user agents on a shared resource overwrite each other.** Give each resource one owner, or
  one coordinator that holds every user's constraints. An agent that does not own a resource
  writes to it only after reading the owner's live state, and a check enforces that, not a
  prompt. Treat any claim about another agent's state that was not read live as suspect.
  [UNVERIFIED] A study of per-user agent teams is said to show this, but we know it only through
  a social-media summary and could not find the paper in four arXiv searches. The rule stands
  without it: one owner per resource, and live state read before any write.
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
the author's lane. The ledger ([#3](https://github.com/rivendale/hsi-operator/issues/3)) and the real
adapter ([#7](https://github.com/rivendale/hsi-operator/issues/7)) landed on 2026-09-24: `hsi record` and
`adapters/ledger/`.

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
