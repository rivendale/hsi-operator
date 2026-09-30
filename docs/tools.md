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
| **Known traps** | See below. | See below. | See below. | See below. |

Where a cell says docs, the pages are Anthropic's Agent SDK overview, OpenAI's
[Codex authentication page](https://developers.openai.com/codex/auth) and its Codex pricing page,
all read 2026-09-23, plus each CLI's `--help` on 2026-09-24. The peer measurements are the
Claude Code allow-list trap (2026-09-05) and the Codex API result (2026-09-24), both below. Everything marked host was measured on one Linux
host. For where the money goes once you drive these tools, see
[`building-a-harness.md`](building-a-harness.md).

## Before trusting any of them

- **Installed is not working.** `--version` and "the binary is on `PATH`" both passed on
  hosts where the CLI could not complete one request; on one check, installed and working
  disagreed on two of three machines (2026-08-06). Prove a CLI with a real prompt ("Reply with
  exactly: PONG") and check the answer.
- **A stale client can fail on the models list, not on your prompt.** An old Codex CLI died
  parsing a reasoning level the server had started advertising, and the error named a model,
  so it read as "that model is unavailable" rather than "this client is too old" (2026-08).
  Upgrade before diagnosing the model.
- **Never install by copying the entry script.** These CLIs ship as JavaScript bundles that
  import sibling chunk files and target one Node major. A copied entry script loses its
  siblings and runs under whatever Node is first on `PATH`; one such copy failed with
  `SyntaxError: Invalid regular expression flags`, which looks like a corrupt download and is
  not (2026-08). Symlink the real bundle, or use a wrapper that `exec`s it.
- **An empty answer may be the invocation, not the model.** `codex exec "..." > file` wrote
  0 bytes and exited 0: the final answer goes to `-o FILE`, not stdout (2026-08-14). The other
  three print it to stdout. Getting this wrong is indistinguishable from a bad model.
- **A scheduled probe must run once as the unit.** A daily real-request probe of every CLI
  failed every scheduled run for three days with exit 127, because its unit set no `PATH`, and
  its failures read as the CLIs being down (2026-09-27). Start a timer job by hand as the unit
  before calling it installed.
- **A tool can state what it cannot observe.** An agent-listing tool labeled a session with
  "the name other sessions use to message it", a claim about other sessions' address books it
  has no view of. Two machines listed the same agent under different names and different ids
  the same minute, and switching to the name the peer's tool printed would have broken a
  working channel silently (2026-09-17). Address a peer by the name your own listing gives it,
  and treat any tool's claim about a remote system as belief, whoever printed it.

## Claude Code

- **Cost fields are client-side estimates.** Anthropic's headless documentation says so, and a
  run started with `--continue` or `--resume` reports the whole conversation's total, so log
  the difference from the previous run (read 2026-09-24).
- **An API key in the environment changes who pays.** With `ANTHROPIC_API_KEY` set, `claude -p`
  always uses the key, billed per token, even when a subscription login exists; interactive mode
  asks once and remembers the answer ([docs](https://code.claude.com/docs/en/authentication),
  read 2026-09-29). Grok CLI does the opposite and keeps its stored sign-in (the matrix above).
  A setup guide that says to export API keys in your shell profile moves every headless run to
  metered billing without a word. Check the environment an unattended job actually runs in, not
  your own shell.
- **`--bare`** skips hooks, plugins, `CLAUDE.md` discovery and auto-memory, and accepts only
  `ANTHROPIC_API_KEY` or an `apiKeyHelper` for Anthropic auth (`claude --help`, 2026-09-24).
  Pass instructions explicitly when you use it.
- **`--setting-sources project,local`** leaves out user-level settings, including user-level
  hooks: a headless run from an empty folder reported no instruction files or hook context
  (2026-09-23).
- **Allow-lists undo deny-lists.** `--disallowedTools` is a deny-list, but adding
  `--allowedTools` re-enables what it blocks, because allow patterns prefix-match. A peer saw a
  worker write a file it was meant to be unable to write (2026-09-05). Use one or the other.
- **A background task can end with the turn, not the work.** A task started with the Bash
  tool's `run_in_background` was killed when the assistant's turn ended, twice, at 9 minutes
  and at 20 seconds, each time to the second of turn end, with a `[killed]` marker written into
  the task's output file (2026-09-05, one host). `setsid` and `nohup` did not escape it, since
  they stay inside the session's cgroup. A job longer than a turn runs under `systemd-run
  --user --collect`, which gives it its own cgroup; check `/proc/PID/cgroup`, then poll the
  unit's state on a later turn, because nothing re-invokes you.
- **A wrapper's exit 0 is not the work.** Backgrounding a command that itself backgrounds
  (`nohup ... &` inside `run_in_background`) reported "completed (exit code 0)" in seconds
  while the real job was still running (2026-09-03). Pick one way to detach. Judge a job by its
  own artifact or the unit's state, and a completion that arrives in seconds for minutes of
  work is the tell. The reverse also happens: a job that dies at admission writes no success
  artifact, so a waiter keyed on that artifact cannot tell "working" from "never started". And
  systemd's `StandardOutput=file:` does not truncate, so a done-marker left by the previous run
  fires a waiter at once; use `truncate:` or wait on `is-active`.
- **Systemd scope.** A worker launched under a systemd scope inherits `INVOCATION_ID`; wrap the
  command in `env -u INVOCATION_ID` if a hook keys on it (2026-09-24).
- **Projects** (claude.ai/code, desktop, mobile; beta): threads are cloud sessions with Anthropic
  as the only model provider, and per the docs "a local session can't be part of a project"
  (read 2026-09-24). New threads are limited to 200 per day, and a project draws on your plan
  faster than one session does.

## Codex CLI

- **An effort level the CLI accepts can be refused by the API.** `codex exec -m gpt-6-luna -c
  model_reasoning_effort="max"` reported `reasoning effort: max` and answered (host, Codex CLI
  0.156.1 on a subscription sign-in, 2026-09-24). The same GPT-6 models called through the Chat
  Completions API with an API key returned 400 and listed the supported efforts as none, low,
  medium, high and xhigh (peer, 2026-09-24). Whether the server applied max or quietly lowered it
  is not observable from the CLI. A setting proven on one path does not carry to another; test it
  on the path your harness will actually call.

## Grok CLI

- **It can exit 0 with no answer.** Headless, it returned one line of narration, exit code 0
  and nothing on stderr (2026-09-24). Require an explicit end marker in the output and treat
  its absence as a failure.
- **To make an API key the credential, remove the stored session.** Setting `XAI_API_KEY`
  does nothing while a stored sign-in exists (the matrix above). What worked was a separate
  `GROK_HOME` holding no `auth.json`, and a wrapper that refuses to run if one appears there,
  because the CLI would prefer it and the key's terms (such as zero data retention) would be
  lost without a trace (2026-08-20). For a day after, two scripts still called the plain CLI,
  so the wrapper existed and nothing used it; grep every call site. **Two balances, one
  watched:** the subscription side returned `402 Payment Required` on every call while the
  same prompt through the key succeeded, so a working key path says nothing about the
  subscription (2026-08-21).
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
