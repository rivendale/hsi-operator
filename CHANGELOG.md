# Changelog

**Every entry names the failure that caused the change.** A line saying what moved is a
diff someone already has; the reason it moved is the part that does not survive anywhere
else, and it is what tells a reader whether the change still applies to them.

Nothing is listed until it is on `main`. Work in an open pull request belongs in the pull
request, because a changelog that describes intentions is a changelog nobody can trust.

Dates are the day the work landed. This project does not ship versioned releases yet; when
it does, the version goes above the date and this line goes away.

## Unreleased

- **The harness guide said how to build a harness but not how to improve one.** Two September 2026
  papers (AIDE-squared, Ecdysis) agree that harness changes should be kept only when they win on
  tasks they were not tuned on, and promoted from recurring failures rather than single ones;
  `docs/building-a-harness.md` now says so, with the stop-and-cleanup behavior a dispatcher needs
  before it runs unattended.
- **An undated failing check lost to any dated proposal, so a known bug could sit behind
  new work (#1).** The owner said, "q3 - failing check i think outranks dated proposal as it
  needs fixing before we move on - i don't want ot leaver bugs/issues behind". Errors with
  direct evidence now rank ahead of every proposal, dated errors by date and undated errors
  by score. Proposals keep deadline-first order among themselves, and reconstructed evidence
  stays held after all direct evidence.
- **The per-tool facts were scattered and partly wrong, and the efficiency guidance lived
  nowhere an agent starting a project would find it (#12).** What each CLI does headless sat
  in one operator's notes, some of it stale (a version, a flag, a billing term). `docs/tools.md`
  now holds it in one dated matrix, and `docs/harness-efficiency.md` holds the efficiency
  checklist, adapted from Cursor's 2026-09-23 article. The same change adds the adapter
  standard (#7), a hand-written ledger row (#3), three testing rules (#13) and the rule for
  when a failure earns a line in `AGENTS.md`.
- **A number recalled from a compacted session could top the board (#6).** `references/l0-channel.md`
  said an item whose evidence is `[RECONSTRUCTED]` must not score; `bin/hsi` ranked one first at 85
  points. It now scores nothing and ranks after every item with direct evidence, dated or not, and
  the board names each held item on its own line, because held back means ranked lower, never
  dropped. A reviewer from another vendor found the first version only matched the marker as an
  uppercase string, so evidence given as a list slipped through; it now matches in any case, in
  strings, lists and objects.
- **A failed check ranked like a new idea (#4).** The board had no way to say an item exists because
  a setpoint's check failed. `signal: error` adds one printed term, `+25 residual`, visible in
  `--why`. An unknown signal is refused like an unknown kind, where before it would have been
  scored silently as a proposal; `null` means no signal. `stale` is refused until the ledger (#3)
  can produce it, because a score term nothing can set is an instrument with one answer. Whether an
  undated error should beat a dated proposal is still an owner decision (#1), so deadline-first
  ordering is unchanged.
- **Nine-tenths of a coordinator's bill was its own context, and nothing here said so.** Two
  long-running sessions priced from their transcripts: re-reading cached context was 60 to 70%
  of cost, cache writes most of the rest, output about a tenth. The advice people reach for
  first (trim the instruction file, shorten answers, fix the cache layout) aims at the smallest
  slices. In one sample every one of 2,819 workflow subagent calls ran on the frontier model
  because no step named a model. `AGENTS.md` now says where the bill goes, and
  `docs/building-a-harness.md` records what a four-model panel and the two samples agreed on
  for anyone building their own harness: drive the vendor CLIs, log cost per call by billing
  type, and enforce review and memory rules in code rather than prose.
- **The loop map still called the fourteen-day check "waiting" after it landed.** Two models
  reading the repo cold found the wiki contradicting this file. `docs/wiki/The-loop.md` now
  matches.
- **A forgotten `CLAUDE.md` switches `AGENTS.md` off, and the documented fix has a trap of
  its own.** Found on an operator's machine the day after we published "one file, no alias":
  a home-directory `.claude/CLAUDE.md` was suppressing a correct `AGENTS.md` beside it, with
  nothing printed to say so. The setting that re-enables both is read only from user-level
  or managed settings, so committing it to a project's `.claude/settings.json` — the natural
  place for a team — fails silently in exactly the shape it was meant to fix. Both now say
  so in `AGENTS.md` and the starter template.
- **The two-week promise is measured now, not asserted (#5, first slice).** The failure:
  the README has promised since day one that going two weeks unopened is the finding, and
  nothing measured it — a claim about our own behaviour that could never come true or
  false. `hsi answered --use FILE` records the day an answer happened; `hsi items.json
  --use FILE` replaces the whole board with one line once that date is fourteen days old.
  It replaces rather than joins, because a fourth item beside three real ones is how a
  warning gets ignored, and a missing file counts as a first run rather than neglect.
- **Unknown flags are refused instead of ignored.** Found while building the above and
  worth more than the feature: `hsi items.json --sittng use.json` used to print a full,
  healthy-looking board while the usage check never ran. A detector that fails open in
  exactly the way it exists to detect is not a detector.
- **`evals/cli/` runs the CLI end to end**, asserting exit codes and output on the real
  commands, with the clock fixed so a case written today still means something in March.
  Three of its twelve checks are refusals. It found one defect immediately — in itself,
  where an assertion tested the wrong capitalisation.

- **The documented install line installed nothing, and exited 0 saying so.** The failure:
  one unquoted colon in the flagship skill's frontmatter made it invalid YAML, so
  `npx skills add` skipped the file, printed "No matching skills found", and returned
  success. The repo named after that skill could not install it. Worse, this repo's own CI
  gate passed it, because the checker read the frontmatter with a regex — a parser that
  accepts what every real parser rejects. Both are fixed: the description is quoted, and
  the check now parses the block as YAML and refuses a file an installer would skip, with
  that mutation added to `--selftest`.
- **Claims corrected against what the repo actually contains.** "Two skills" above a list
  of three; a pointer to `examples/AGENTS.example.md`, which this repo moved and never
  re-pointed; "every tool loads AGENTS.md" three lines above a table showing one that does
  not; "no CI gate" after CI was added; and five files still assigning an agent to issue
  #2, which shipped on 2026-09-21. A repo about checking claims against reality was
  carrying five that a reader could falsify from the same page.
- **Trust does not nest, and trusted-with-zero is still unguided.** Both measured, both
  added to the tool table, and both the kind of gap that looks like success.
- **The tool this file recommends by name now carries its data path, with a version and a
  date.** A public file that recommends a tool owes the reader what it transmits; an
  undated claim about someone else's software is wrong the day they change it.

- **One instruction file, and no alias.** The failure this replaces: the repo told readers
  to keep a second per-vendor filename symlinked to `AGENTS.md`, hedging against tools that
  had not caught up. Measured instead of assumed, every tool this repo is worked with loads
  `AGENTS.md` — so the hedge was advice to maintain a name nobody needs. A tool that reads
  only some older name is now a measurement to record in the table, not a second file for
  everyone to carry.

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
