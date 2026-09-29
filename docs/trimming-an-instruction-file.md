# Trimming an instruction file by evidence, without losing the rules that work

Written 2026-09-29 from one public case, read from its pull request, and one tool, read from its
source. We ran neither.

## The case (the author's account; figures re-read from GitHub on 2026-09-29)

[kunchenguid/firstmate#5872](https://github.com/kunchenguid/firstmate/pull/5872) (MIT; merged
2026-09-27; +403/-287 across 14 files in 3 commits) moved situational sections of the repo's
`AGENTS.md` into skills that load on demand. The edits were proposed by
[backpass](https://github.com/kunchenguid/backpass) (MIT; v0.1.30 released 2026-09-29), which
mines session transcripts for evidence about each instruction. Measured through GitHub's contents
API, `AGENTS.md` went from 89,921 bytes at the base commit to 47,958 at the head.

What held up: nothing was deleted outright, every removed line survives in a skill, two of the
proposed extractions are not in the merged change, and a live side-by-side check ran after the
edits.

What to learn from it:

- **The whole saving rested on the weakest evidence.** In the tool's proposal, each of the 10
  extractions cited one quote from one session: moving text into a skill was exempt from the
  two-session floor that additions and rewrites had to meet.
- **Absence of evidence is what a working prohibition looks like.** A rule that prevents
  something leaves no trace in a transcript. The PR's third commit, "close load-timing gaps found
  by the live regression check", put three rare but critical rules back inline and made one
  extracted skill load on every ask-the-user answer. Those edits had passed the tool's gates. Only
  the behavioral check caught them. (The PR body says the check "found no core-behavior
  regression"; read that as core behavior, not every rule.)
- **A quote found in the transcript is not a quote that supports the edit.** The check proves the
  text exists, not that it means what the edit's explanation says.
- **The editor ran under the file it was editing,** and its summary picked up the file's persona.
  Keep the agent that edits out of the context it is editing.
- **Transcripts leave the machine.** Read at v0.1.29, the tool sends distilled transcripts to
  whichever vendor its model ladder picks, and redacts only secret-shaped strings: names,
  addresses and account numbers pass through. Pin the backend, and read what gets sent, before
  pointing a tool like this at transcripts that mention people.

## The method, by hand or with a tool

1. **Measure the whole surface loaded at start, not one file:** the instruction file, every skill
   description, any memory index, and hook output. In one long-running setup we measured, the
   instruction file was under a fifth of about 105 KB loaded at start; the skill listing and the
   memory index were each larger.
2. **Use one ruler.** A percentage does not change with the divisor, so two close figures for one
   change can still mean two different things were measured: in this case, the proposal's -48% was
   the whole surface as proposed, and the PR's -47% was the one file as merged.
3. **Sort each negative into harm or non-compliance.** A rule that was skipped needs rewording or
   reinforcing. Being skipped is not evidence for deleting it.
4. **Two independent sightings before adding or rewriting a rule,** and a written reason for every
   rejection, so it is not proposed again. This repo's [`AGENTS.md`](../AGENTS.md) applies the
   same test ("How a rule gets into this file", under Testing).
5. **Keep a protected list that is never a candidate** for removal or extraction: prohibitions,
   safety rules, anything irreversible. Protect it with structure, such as a check that rejects any
   change touching it, not with one line in the editor's prompt.
6. **Build the regression guard before the first edit, with a different agent:** one refusal probe
   per protected rule, each proven to fail on a known-bad answer, plus a held-out set of decision
   moments with the expected behavior written down first. Change the file in one round and measure
   in another, never both at once.
7. **Check from the consuming end:** in the next fresh session, confirm what actually loaded and
   that every refusal probe still refuses.

Claude Code now includes `/doctor prompt-audit` (v2.1.283 or later;
[docs](https://code.claude.com/docs/en/memory), read 2026-09-29). It reads instruction files,
rules and skills, looks for instructions written for older models, references to files that do not
exist and files that contradict each other, and changes nothing until you ask. Its proposals need
the same guard.
