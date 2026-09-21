# AGENTS.md — how agents work in this repo

**One file: `AGENTS.md`. No second name, no symlink, no fork.** Every tool this repo is
worked with loads it, and that is a measurement rather than a vendor's promise.

Measured 2026-09-21, by asking each tool what it loaded rather than reading a release note:

| tool | version | instruction file | skills |
|---|---|---|---|
| Claude Code | 2.1.278 | `AGENTS.md` | `~/.claude/skills`, `.claude/skills` |
| grok | 1.0.34, then 1.0.40 hours later | `AGENTS.md` — **but only inside a folder it trusts**; an untrusted directory reports `Project Instructions (0)`, which reads exactly like "there is no instructions file" | reads `~/.claude/skills` |
| Gemini CLI | 0.60.0 | its own file | its own store: `gemini skills install <git url>`, and it does **not** see `~/.claude/skills` |
| Codex CLI | 0.155.1 | `AGENTS.md` | plugins: `codex plugin add`, from a marketplace |

Two instruction files drift, and the auto-loaded one wins the contradiction, so there is one
file and no alias. If you meet a tool that reads only some older name, that is a measurement
to record here — not a reason to keep a second copy for everyone else.

Two more things measured the same way, on three machines:

- **An `@other-file.md` import line is not expanded by every tool.** One tool left the
  literal string in place and found the target file on its own, so the same content appeared
  as two entries. The content arrived; the mechanism the file implies was not the one that
  delivered it. Do not assume an import works for a reader you have not asked.
- **A version measured at the start of a session may not be the one that ran.** One of these
  tools updated itself from 1.0.34 to 1.0.40 between two measurements a few hours apart, with
  no prompt. Date every version claim, and re-read it before citing it.
- **On a case-insensitive mount, one instruction file can load twice.** The same file was
  listed under two casings and counted at full token cost each time. A figure measured there
  is double; measure on the native filesystem.

**Prove the load, not the filename.** "Nothing loaded" and "no file here" print the same
string. A first pass at this table had grok ignoring `AGENTS.md`; a peer showed the real cause
was an untrusted folder, and a controlled probe inside a trusted root then loaded `AGENTS.md`
alone without complaint. Before blaming a name, drop a two-line file in that directory and ask
the tool what it loaded. A project directory the tool does not trust is silently unguided:
every rule in this file is absent and nothing says so.

The repo's substance is in `skills/`. This page is the working agreement around it.

---

## Scope guard

**Complete the task with the smallest sufficient change.** An explicit instruction for the
task at hand overrides every default below. Adapted from the scope-guard snippet circulating
for `AGENTS.md`, rewritten rather than copied.

**Before editing.** Read the relevant code, its call paths and the project's conventions.
Do not read the whole repository before a small change. Make small, clear fixes directly;
write a short plan only when the approach is unclear or the blast radius is large. Decide
routine details yourself, and ask when two readings of the request would produce materially
different work. Load the one skill that fits, not a whole workflow because a keyword matched.

**While editing.** Before writing new code, look in this order: what the project already
does, the standard library and platform, dependencies already installed, and only then
something new. Fix the root cause. Do not add abstractions, configuration or compatibility
layers for needs nobody has today. Justify a new dependency by saying why the existing
options fail. Touch a nearby bug only if it blocks the task; otherwise write it down. Prefer
a precise edit to a rewrite, delete what you replaced, and keep the validation, error
handling, security and accessibility that were already there.

**When to ask.** Keep implementing, verifying and fixing inside the scope you were given;
do not ask permission to continue. Ask before expanding scope, spending money, taking a new
permission, or doing something irreversible or outward-facing. If you were asked to review,
report findings and do not edit.

**If the plan grows,** and you notice future-only layers, unrelated refactoring or extra
features, drop them and finish the thing that was asked for.

**Done means** the requested behavior works, the verification is done, the temporary files
are gone, and the report says what was verified and what was not.

---

## Testing

**Never write unit tests after writing the code.** A test written by whoever just wrote the
implementation is the author grading their own homework: it encodes what the code does, not
what it should do, and it passes for that reason. The ground truth has to come from outside
the thing being graded.

- **Prefer end-to-end tests as the main mechanism.** Drive the real interface the way a user
  does, and have the run leave a **verifiable, repeatable artifact** — an exit code, a file,
  a screenshot, a number someone else can reproduce.
- **If a piece genuinely needs isolation, write the failure list first.** Enumerate every way
  it could fail, in writing, *before* the implementation exists. Then build against that list.
- **Reuse the tests that exist** before adding new ones, and add tests for real behavior and
  regression risk rather than tests that restate the implementation line by line.
- **A temporary verification script does not have to become a permanent test file.**
- **Prove the rule in the denying direction.** A check nobody has seen refuse anything is a
  check that has not been tested. Feed it an input it must reject.
- **Vary the fault.** Making one hand-picked mutation fail proves sensitivity to that
  mutation, not coverage. Include omissions and stale artifacts, not just corruptions.
- **Ask what the check would print if the thing were broken.** A harness that can only ever
  print one answer is worse than one that fails loudly, because it cannot be argued with.
- **Test from the consuming end.** The expensive failures all share one shape: success
  declared at the producing end while the intended consumer never received the effect.

---

## Context and what it costs

A long context window is a bill, not just a limit.

- **An uncached request against a very large window costs real money** — single-digit dollars
  per request at the top end, and a subscription quota drains the same way. The common way
  into it is walking away from a long session and coming back after the prompt cache has
  expired (on the order of an hour, shorter on some tools).
- **Compact before you walk away, not after you come back.** Compacting a cold, huge window
  is itself a full-price request, so it costs the thing you were trying to save.
- **Coming back to a cold, large window, prefer a new session** and point it at the previous
  session's transcript if it needs the detail.
- **Compact at a boundary**, when a unit of work is finished, and require less certainty as
  the window fills. `skills/context-steward/SKILL.md` has the rule and the arithmetic;
  [compact-adviser](https://github.com/kunchenguid/compact-adviser) (MIT) is a plugin that
  makes that call for you.
- **Move detail out to a path rather than summarizing it away.** A summary is a pointer, and
  a bad one: it drops the file path, the exact error and the number, silently.

---

## Working with the person

The skills say this at length. The short version for anyone editing here:

- **Three items, ranked, with the ranking rule printed.** A list of twenty-seven is a list of
  zero.
- **An item asking a person for a fact is a search somebody skipped.**
- **State the absence.** "Nothing needs you" is the update, not the lack of one.
- **Label the basis of a claim**: Data, Estimate, Assumption, Opinion. Never present an
  estimate as data. `skills/hsi-operator/references/honesty-protocol.md`.
- **Give a verdict**, especially a negative one. A list of considerations is work handed back.
- **Findings, not directives**, when the thing belongs to someone else: send what you
  measured and let the owner sequence it.
- **Write decisions down with the date and the reasoning**, in the decider's words. A verdict
  without its reasoning cannot be applied to the next case.

---

## Visual work: image first

For anything whose output is seen rather than run, generate and refine the **image** first,
then implement from it. Judging a picture is fast and cheap; judging a page by reading the
code that produces it is neither. Tools with a strong image model built in make this a single
step: ask for the design, iterate on the image, then implement the version you accepted.

---

## Skills

- **Install the skill you need, not a bundle.** `skills/` here is three skills, each one file
  plus a small script.
- **Pin an installed skill to a reviewed commit rather than tracking `main`.** A skill is
  instructions: tracking a branch means a future push edits how an agent behaves with no
  review step on that machine. Check out a reviewed SHA, read the diff, then move the pin.
- More skills, and the conventions they follow: [anthropics/skills](https://github.com/anthropics/skills).

---

## Secrets

Report **where** a credential lives, never what it is. Never pass a secret as a command-line
argument, and never print one into a transcript or a log. A secret's location may survive
into notes and handoffs; its value never does.

---

## Honest limitations of this page

- None of it is enforced. There is no hook, no CI gate and no lock. It is a rule someone
  keeps, and a rule nobody keeps is a comment.
- The cost figures are the right order of magnitude, not a price list; vendors change both
  prices and cache lifetimes.
- `examples/AGENTS.example.md` is the copyable version for another repo. This one describes
  *this* repo and is not a template.
