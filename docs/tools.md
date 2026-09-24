# The four coding CLIs, measured

What each tool actually did when driven headless. Every cell ends with its source and date.
Versions checked 2026-09-24: Claude Code 2.1.281, Codex CLI 0.156.1, Grok CLI 1.0.41,
Gemini CLI 0.60.0. A cell says "not checked" where nobody here has looked; that is different
from "no". "Undated" means the source recorded the observation without a date. Vendors change
flags and billing terms, so re-read a cell before you build on it, and add the date when you do.

Source tags used in every cell:

- **host**: measured by this repo's operator on one Linux host; the date is the one recorded.
- **peer**: measured on a peer's machine and reported to the operator.
- **docs**: a vendor's documentation, or the CLI's own `--help` output, read on the date given.
- **[AGENTS.md](../AGENTS.md)**: recorded there with the date given; the link is the source.

How each tool loads an instruction file, and the traps in proving it, is measured in
[`AGENTS.md`](../AGENTS.md); the first row only points there.

## Matrix

| | Claude Code | Codex CLI | Grok CLI | Gemini CLI |
|---|---|---|---|---|
| **Instruction file, and proof it loaded** | `AGENTS.md`. A `CLAUDE.md` in any directory above switches it off silently. Prove it by asking the session what it loaded. ([AGENTS.md](../AGENTS.md), 2026-09-21) | `AGENTS.md` from the repository. Proof: ask the session. ([AGENTS.md](../AGENTS.md), 2026-09-21) | `AGENTS.md`, only in a trusted folder. Proof: ask the session; "instructions: 0" means the rules are absent. ([AGENTS.md](../AGENTS.md), 2026-09-21) | Its own filename, not `AGENTS.md`. Proof: ask the session. ([AGENTS.md](../AGENTS.md), 2026-09-21) |
| **Trust** | Not checked. | Refuses a non-git scratch directory as untrusted; a git worktree works. (host, 2026-09-05) | Each checkout needs its own trust entry; a trusted parent does not cover it. ([AGENTS.md](../AGENTS.md), undated) | Refuses to run in an untrusted directory. (host, undated; recheck) |
| **Headless run** | `claude -p`. (host, undated) | `codex exec -m MODEL -s read-only\|workspace-write -o FILE --json -`, prompt on stdin. (host, undated) | `-p TEXT` for a one-shot, `--prompt-file FILE` for a long prompt. (host, undated) | `gemini -p ""` with the prompt on stdin. (host, undated) |
| **Read-only mode** | `--permission-mode plan`, listed by `--help`. (docs, 2026-09-24) | `-s read-only`. (host, undated) | `--permission-mode plan`, listed by `--help`; behavior not checked. (docs, 2026-09-24) | `--approval-mode plan`. (host, undated) |
| **Edit mode** | `--permission-mode acceptEdits`, listed by `--help`. (docs, 2026-09-24) | `-s workspace-write`: writes the working directory, `/tmp` and `$TMPDIR`; network off, including a localhost socket, unless `-c sandbox_workspace_write.network_access=true`. (host, 2026-09-24) | `--permission-mode acceptEdits`, listed by `--help`. (docs, 2026-09-24) | Not checked. |
| **Structured output and cost fields** | `--output-format json`: `total_cost_usd`, `usage` (input, output, cache read, cache creation with a 5m/1h split), `modelUsage`. (host, a real run, 2026-09-24) | `--json` streams events with token counts (input, cached input, output). No dollar figure. (host, undated) | `--output-format json`: `text`, `usage` (input, cache read, cache creation, output, reasoning tokens), `total_cost_usd`, `stopReason`. Other values: `plain`, `streaming-json`, `streaming-messages-json`. (host, 2026-09-24) | Not checked. |
| **Sign-in and billing** | Your own CLI on your subscription is the normal path; products built on the Agent SDK use API keys. (docs, Anthropic Agent SDK overview, read 2026-09-23) `--bare` never uses the subscription login. (docs, `claude --help`, 2026-09-24) | ChatGPT sign-in is subscription access; an API key is usage-based; OpenAI recommends the key for CI. (docs, [Codex auth](https://developers.openai.com/codex/auth), read 2026-09-23) Allowances differ by model. (docs, Codex pricing page, read 2026-09-23) | Prefers a stored sign-in session over `XAI_API_KEY` in the environment, with no error. (host, 2026-09, no day recorded) | New individual Google sign-ins were refused with `IneligibleTierError`; existing credentials kept working. (host, 2026-09-08) |
| **Version drift** | 2.1.278 on 2026-09-21 ([AGENTS.md](../AGENTS.md)); 2.1.281 on 2026-09-24 (host). It updates itself. | 0.155.1 on 2026-09-21 ([AGENTS.md](../AGENTS.md)); 0.156.1 on 2026-09-24 (host). | 1.0.34 to 1.0.40 within hours on 2026-09-21 ([AGENTS.md](../AGENTS.md)); 1.0.41 on 2026-09-24 (host). | 0.60.0 on 2026-09-21 ([AGENTS.md](../AGENTS.md)) and on 2026-09-24 (host). |
| **Known traps** | See below. | Not checked beyond the rows above. | See below. | See below. |

Where a cell says docs, the pages are Anthropic's Agent SDK overview, OpenAI's
[Codex authentication page](https://developers.openai.com/codex/auth) and its Codex pricing page,
all read 2026-09-23, plus each CLI's `--help` on 2026-09-24. The one peer measurement is the
Claude Code allow-list trap below (2026-09-05). Everything marked host was measured on one Linux
host. For where the money goes once you drive these tools, see
[`building-a-harness.md`](building-a-harness.md).

## Claude Code

- **Cost fields are client-side estimates.** Anthropic's headless documentation says so, and a
  run started with `--continue` or `--resume` reports the whole conversation's total, so log
  the difference from the previous run (read 2026-09-24).
- **`--bare`** skips hooks, plugins, `CLAUDE.md` discovery and auto-memory, and accepts only
  `ANTHROPIC_API_KEY` or an `apiKeyHelper` for Anthropic auth (`claude --help`, 2026-09-24).
  Pass instructions explicitly when you use it.
- **`--setting-sources project,local`** leaves out user-level settings, including user-level
  hooks: a headless run from an empty folder reported no instruction files or hook context
  (2026-09-23).
- **Allow-lists undo deny-lists.** `--disallowedTools` is a deny-list, but adding
  `--allowedTools` re-enables what it blocks, because allow patterns prefix-match. A peer saw a
  worker write a file it was meant to be unable to write (2026-09-05). Use one or the other.
- **Systemd scope.** A worker launched under a systemd scope inherits `INVOCATION_ID`; wrap the
  command in `env -u INVOCATION_ID` if a hook keys on it (2026-09-24).
- **Projects** (claude.ai/code, desktop, mobile; beta): threads are cloud sessions with Anthropic
  as the only model provider, and per the docs "a local session can't be part of a project"
  (read 2026-09-24). New threads are limited to 200 per day, and a project draws on your plan
  faster than one session does.

## Grok CLI

- **It can exit 0 with no answer.** Headless, it returned one line of narration, exit code 0
  and nothing on stderr (2026-09-24). Require an explicit end marker in the output and treat
  its absence as a failure.
- **Turn budget.** A review brief run with `--max-turns 14` ran out and returned narration;
  40 has been the working budget (2026-08-18).
- **Fixed overhead.** A one-word prompt cost about 30,000 input tokens, because the CLI's own
  instructions and tool definitions ride on every call (2026-09-24).
- **A prompt flag that looks like a broken CLI.** An older `--prompt` flag failed with a help
  message (2026-08). Use `--prompt-file`.
- **Slow and thorough on one brief.** As a reviewer it took 23 minutes and reported 0.75 USD,
  against about 2 minutes and 0.40 USD for Claude Sonnet 5 on the same brief, and it found more
  by running its own fixtures (2026-09-24). One brief, so an anecdote, not a rate.

## Gemini CLI

- **A healthy host can be one sign-in from broken.** Existing credentials kept working while a
  new individual sign-in was refused (2026-09-08). It answered a live request on an existing
  sign-in on 2026-09-24.
- **No `~/.claude/skills`.** It has its own skill store (measured in [`AGENTS.md`](../AGENTS.md)).

## Roles that held up

One operator's records, 2026-09. Small sample; treat as a starting default.

- **One model implements; a model from a different vendor reviews.** Settle disagreements by
  reading the source, not by vote: a three-model review once went 2 to 1 the wrong way.
- **Ask a reviewer to verify named claims, not "is anything wrong?"** Grok tended to answer no
  to the open question and missed defects; on named claims it was strong.
- **Expect each model's habit.** Gemini found real defects and overstated their severity.
  Codex built working code and did not audit what its own change deleted.
- **A reviewer with no shell cannot run the code or git.** Put the diff in the prompt.
