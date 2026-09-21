# Changelog

**Every entry names the failure that caused the change.** A line saying what moved is a
diff someone already has; the reason it moved is the part that does not survive anywhere
else, and it is what tells a reader whether the change still applies to them.

Nothing is listed until it is on `main`. Work in an open pull request belongs in the pull
request, because a changelog that describes intentions is a changelog nobody can trust.

Dates are the day the work landed. This project does not ship versioned releases yet; when
it does, the version goes above the date and this line goes away.

## Unreleased

- **`starter/` and `docs/adopting-an-existing-repo.md`.** The failure this guards against
  is the one every rules file invites: sixty lines pasted on day one, followed by nobody
  citing any of them. The starter is four files for an empty repo; the adoption guide is
  for a repo with habits already in it, ordered so each step is paid for by a failure you
  can name, with a way to tell whether it worked and an instruction to stop when it is not.
  `examples/AGENTS.example.md` moved to `starter/AGENTS.md` rather than being copied, so
  there is one of it.

- **`evals/trigger/`, and the repo's first CI.** The failure: a skill is loaded by its
  description and nothing else, so a perfect body behind a description missing the words
  people type never runs — and nothing here checked that. It found the defect immediately:
  "is this library worth installing" routed to `context-steward`, not `repo-triage`.
  Two rounds of independent review then found the check itself was the softer problem: its
  cases were paraphrases of the descriptions they graded, which is the author marking their
  own homework, and its contrast set scored zero, which made the margin unreachable. Cases
  are now written from outside the description, the scoring is coverage rather than a
  length-damped count, a case that only a semantic router could catch is marked non-lexical
  rather than quietly lowering the bar, and `--selftest` re-runs four real mutations so the
  denying-direction evidence is a command rather than a paragraph in a pull request.

## 2026-09-21

- **Door 2 became a file: the setpoint contract and `hsi done` (#9).** The failure: Door 2
  was prose, so nothing could compare an outcome to it and no agent could be asked to cite
  it before starting. A setpoint is one JSON object with an `id` to cite, a `check` that is
  a command, a number or a person, and `invalidated_by` — a condition, never a timer.
  `hsi done` prints the five answers and exits 2 when done has no external check, because
  "it looks good" is not checkable. The interlock is a rule, not a lock: no work starts
  without a setpoint id.
- **`AGENTS.md`, and a copyable example (#11).** The failure: instructions for agents were
  spread across a README, three skills and whoever remembered. One file now carries the
  scope guard, the testing discipline, what a long context costs, and how to talk to the
  person — with a table of what each tool actually loads, measured by asking the tools
  rather than reading release notes. Two of those measurements were wrong first: a claim
  that one tool ignores the `AGENTS.md` name turned out to be folder trust, and a version
  in that table changed under us mid-session. Both corrections are in the file.

## 2026-09-18

- **`hsi-operator` skill, both doors.** The failure: agents are good at producing things
  and bad at knowing whether anyone wanted them, so they either surface everything as
  important or surface nothing and build the wrong thing. Door 1 returns three ranked
  items, each phrased as an answerable question, and prints the ranking rule so the
  judgment can be audited. Door 2 asks what done means *before* building, and biases toward
  a smaller done rather than a more rigorous plan.
- **`bin/hsi` and a plain JSON contract.** The failure: a tool that knows your tracker is a
  tool nobody else can use, and a ranking nobody can recompute by hand is a ranking nobody
  trusts. The CLI reads plain JSON, scores on four printed terms, and `--why` shows the
  arithmetic for any item. An adapter, not the skill, knows where your work lives.
- **A generic adapter shipped instead of ours.** The failure: the first version read a
  private estate's file layout, which makes a public tool a private tool with an audience.
  `adapters/jsonl-tasks/` reads a line-delimited task file and says plainly that an adapter
  over structured data cannot know *why* an item needs a person.
- **Four-way claim labelling, from `ferdinandobons/startup-skill` (MIT, credited).** The
  failure: collapsing *estimate* into *assumption* is what lets a calculation pass as a
  finding. Data, Estimate, Assumption, Opinion, with the honesty protocol that also
  requires stating an absence rather than omitting a section.
- **`repo-triage` skill.** The failure: adopting on enthusiasm. A shared link arrives with
  stars and a launch post, and the only question that matters is whether it closes a gap
  you measured. Cheapest kill first: licence, then maturity, then whether the runtime
  exists on the hardware you actually have.
- **`context-steward` skill.** The failure: compaction summarizes, and a summary silently
  drops the file path, the exact error and the number. Move detail out to a path instead,
  act at 80% rather than 95%, and mark anything rebuilt from a summary as
  `[RECONSTRUCTED]`.
- **`context-steward`: when to compact, not just what to keep.** The failure named by
  [compact-adviser](https://github.com/kunchenguid/compact-adviser) (MIT, credited): a
  wrong "compact now" costs most while there is still room, so the certainty required
  should fall as the window fills.
- **`context-steward`: a secret's value never survives, and durable notes go to a private
  repo only.** The failure, found in review: the skill told an agent to write working
  memory somewhere durable and ranked "the repo" first, while this repo is public — so a
  handoff would have published names, locations and the status of other work. A live
  credential in a long session also scores as important enough to keep.
- **`references/allocation.md`, `references/l0-channel.md`, `references/hsi-se.md`, and the
  `docs/wiki/` pages.** The failure: the person-test was a paragraph, so every new rule
  risked inventing policy in the ranker. Function allocation, the operator channel and the
  systems-engineering prior art are now written down, including what we refused to take.
