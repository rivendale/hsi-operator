# Changelog

**Every entry names the failure that caused the change.** A line saying what moved is a
diff someone already has; the reason it moved is the part that does not survive anywhere
else, and it is what tells a reader whether the change still applies to them.

Nothing is listed until it is on `main`. Work in an open pull request belongs in the pull
request, because a changelog that describes intentions is a changelog nobody can trust.

Dates are the day the work landed. This project does not ship versioned releases yet; when
it does, the version goes above the date and this line goes away.

## Unreleased

- **Agent replies were correct but slow to act on: one setting called three things, warnings
  before the command, 40- to 54-word sentences, and banned em dashes in 11 of 40 sampled replies
  because nothing checked.** New `docs/plain-writing-for-agent-output.md`: six ASD-STE100 rules
  chosen by scoring 40 replies against 11 rules (with the counts), the five rejected and why, and a
  warn-only check for the three mechanical ones.

- **Every merge re-ran the full eval job on main, on content its pull request had just
  passed: 14 of the last 40 runs (2026-09-26 to 10-02), and a superseded push kept running
  beside its replacement.** `evals.yml` now cancels an outdated run on the same branch, and
  after a merge it skips `trigger` only when it can prove the merged tree is the one a pull
  request run passed. The PR run records that tree as the `evals/tested-tree` commit status;
  a direct push, a fork PR, a base that moved or an API error cannot prove it, so those run
  everything as before. `siblings` always runs after a merge, because the sibling repos are
  inputs this tree does not pin.

- **An operator lost track of what their own live app did: which jobs ran with nobody
  watching, where an output fed back into its own input, and which promised notices never
  reached a person. Nothing in this repo could map a system, and a diagram drawn by a model
  from a vague prompt invents boundaries in exactly the places nobody checks.** New
  `skills/system-map/`: triggers first, then components, stores, flows, human touchpoints
  and feedback loops, every claim cited to a file and line or a dated live check, rendered
  as one zoomable HTML map. The map is the measurement half of the loop Door 2 already
  sets: drift between setpoint and map becomes DECIDE items for Door 1 via `sysmap items`.
  `bin/sysmap check` refuses an uncited, dangling or self-contradicting map, a cited secret
  file and a credential-shaped string, and with `--src` a cited line that does not exist.
  `sysmap render --vendor-dir` builds a page that makes no CDN request, and refuses a
  library whose local copy does not match its pinned hash. `sysmap selftest` proves each
  refusal and now runs in CI. The schema's own example is the selftest's input, so the
  documented contract cannot drift from the checked one.

- **The repo meant to be the one a person points an agent at named one of its three sibling
  repos, once, inside a docs page, and no sibling linked back: an agent sent here never learned
  that local-ai or homelab existed, and a reader who landed on a sibling never found the hub.**
  `README.md` and `AGENTS.md` now open with a "start here" table saying what each sibling is
  for and when to read it, and `repos.json` holds the same routing facts for a program.
  `evals/siblings/run.py` fails when either page stops linking a sibling, when a marketplace
  entry for a sibling has no 40-hex `sha` or its description drifts from `repos.json`, and,
  given the siblings' checkouts, when a sibling's `README.md` or `AGENTS.md` does not link
  back here within its first 12 lines; `--selftest` proves each of its 19 refusals and 3
  passing verdicts. A new `siblings` CI job clones each sibling and runs both. The check lives
  under `evals/`, not a top-level `bin/`, because this repo is its own plugin root and a
  plugin's `bin/` joins the Bash tool's `PATH` while the plugin is enabled.

- **`.claude-plugin/plugin.json` set `"version": "0.1.0"` in its first commit and never changed
  it, so anyone who installed the plugin through its marketplace stayed on that first copy
  through every later commit: Claude Code takes the manifest's version first and treats an
  unchanged version as no update.** Measured from a clean home directory against a copy of
  this repo: after a new commit to a skill, `claude plugin update hsi-operator@rivendale`
  printed `hsi-operator is already at the latest version (0.1.0).` and the installed copy
  lacked the change. `version` is removed, so the version is the commit, which is what the
  pin rule in `AGENTS.md` already asks a reader to review; `evals/siblings/run.py` refuses a
  `version` in `plugin.json` or in any marketplace entry. `README.md` gains the plugin install
  from a pinned clone. Documented behavior:
  [plugin versions](https://code.claude.com/docs/en/plugins/loading#versions-and-updates).

- **The starter told an agent in a code repo to make the smallest change, and nothing about
  where logic belongs: a refactor could ride in the same commit as a behavior change, a
  second copy of a price rule or model name could be written beside the first, and a rule
  could be added to the instruction file with no check behind it.** New
  `docs/design-rules-for-code.md` holds six rules for code, each with its check or an honest
  "review only": reorganize first then change (with an output diff for high-stakes
  calculations), one owner per fact (a function-level import dodging a cycle means misplaced
  logic), grep for the expression rather than the function name before reuse, no business
  logic in display code, the lowest-future-cost tie-break stated in the commit, and gates
  rather than promises with three worked checks; plus what to leave out (generic principle
  lists, self-reported before-and-after numbers). `starter/AGENTS.md` gains a compact Design
  rules section; `AGENTS.md` points to the page from the scope guard and extends Testing's
  "mechanical check" item to rules being added; `README.md` lists the page. The framing,
  design principles as hard rules in `AGENTS.md`, is Tomas Vykruta's (@tvykruta on X,
  2026-09-30).

- **Eight additions from one operator's working notes, where they helped only that operator's
  agents: a cause settled on with no rival named, a merge gate that could have moved to a model
  whose reasoning is harder to monitor, a skill installed at whatever version the registry served,
  a compaction prompt with no list of what to keep, an instruction-file trim that found almost
  nothing to trim, reviewers who saw a diff but not the decisions or validation behind it, a
  per-request router choosing for a stronger model, and a vendor chart crowning the vendor.**
  `AGENTS.md` gains rival explanations (Testing), installing third-party skills from a pinned local
  clone (Skills) and the six things a summary prompt keeps (Context); `tools.md` gains picking a
  review lane's model by role, with chain-of-thought controllability figures from a system card;
  `trimming-an-instruction-file.md` gains auditing before assuming there is steering prose to
  delete; `writing-a-brief.md` gains the pull request as the reviewer's brief (decisions on the PR,
  honest validation, repeated comments become checks); `choosing-effort.md` gains letting the lead
  agent choose tier and effort per subagent instead of a router; `eval-and-hillclimb.md` gains
  asking whether a benchmark's publisher sells the winner.

- **Eleven more lessons, each from a failure someone published or measured: a compressed tool
  output that made the task dearer, a prompt trim that turned parallel work serial, LLM routers
  caught injecting code (9 of 428 tested) or touching planted credentials (17 of 428), malware
  hiding in agent settings folders, compromised packages behind valid build attestations, and a memory store whose first contradiction check found five
  conflicts.** `building-a-harness.md` gains items 13 to 15 (checked batching, no third-party
  router between agent and provider, read a clone's agent settings before opening it) and a
  self-updating memory under "Where this goes wrong"; `harness-efficiency.md` gains GitHub's three
  cost results (measure the finished task, evidence is local to the workload, a shorter prompt can
  delete an untested behavior); `AGENTS.md` gains comments as claims, mechanical checks for rules
  an agent agrees with and still breaks, and triggers for known limitations; `tools.md` gains that
  naming a model in an instruction file does not switch it; `planted-defect-evals.md` gains
  record-and-replay before a rewrite; `eval-and-hillclimb.md` gains checking a public benchmark
  against an independent review before relying on it.

- **The wiki page claimed a mirror that did not exist, and running the evals left bytecode to
  commit.** `docs/wiki/Home.md` said its pages were mirrored to the GitHub wiki, which on
  2026-09-30 still held only its default page. It now says the repo copy is the only current one
  and any mirror is manual. A `.gitignore` covers `__pycache__/` and `*.pyc`, which the Python
  evals write and nothing excluded.

- **Twenty lessons that a stranger could use sat in one operator's private notes, where only
  that operator's agents could learn from them, and the eval page still called itself a draft
  after its first run.** Each lesson came from a real failure: an auth check that read HTTP 200
  while the server refused the key in the body, a hook guard that never reached the always-on
  session it was written for, a filter hardened through 21 review rounds that had never received
  one line of input, four secret scans that agreed on a wrong count over a clone missing
  pull-request refs, a redaction line that printed the token it was hiding, a grader that failed
  answers for naming the trap they avoided. They are now in `building-a-harness.md` (hooks never
  ask, scope enforced by tools, guards and long-lived sessions, status-code auth checks),
  `planted-defect-evals.md` (a checker must reach several verdicts, old code against the new
  test, prose detectors), `read-only-audit.md` (count the input, fetch pull-request refs, diff
  against the prior version, one clock), `tools.md` (installed is not working, tools asserting
  what they cannot see, background jobs and wrapper exits, Grok's stored session),
  `writing-a-brief.md` (the latest message, mid-run redirects, handoffs as attacks),
  `harness-efficiency.md` (fan-out results land in the parent), `adopting-an-existing-repo.md`
  (an unlicensed control looks forgotten) and `AGENTS.md` (grants invisible until restart, the
  redaction idiom, inspection commands that dump secrets). `eval-and-hillclimb.md` loses its
  draft marker and records what its first run showed: most of the cost was a cache never read,
  lower effort cost recall but not precision, and the optimized call had no consumer until
  someone checked.

- **Lessons measured over two weeks lived only in one operator's private notes, and two had
  drifted while they sat there.** A benchmark figure copied from a screenshot (Sonnet 5.5 at
  xhigh, $1.55 per planted bug) came from one run; the raw data, re-read the day this was
  written, gives $1.19 over three. A proposed one-liner said a change of effort clears the prompt
  cache, and its correction said it keeps it; Anthropic's two posts describe two different paths,
  and each was right about one. Seven pages in `docs/` now carry these lessons with every source
  dated: choosing effort, writing a brief, trimming an instruction file, planted-defect evals,
  eval and hillclimb (a draft until its first run), naming the reader, and a read-only audit.
  `building-a-harness.md` item 8 gains five review rules and a new item 10 covers atomic handoff;
  `AGENTS.md` gains the silent size budgets, a generator that writes its own `AGENTS.md`, the
  first-party pin question and motion storyboards; the starter, `tools.md` (an API key changes
  who pays) and three skill bodies get a line or two each. No skill description changed.

- **The link check went red on `main` after passing on its own pull request (#38).** A
  documentation site now redirects to a host that serves a bot challenge, answering 403 to the
  runner while a browser still gets the page. A check that flips on a host's bot rules is not a
  link check, so the workflow excludes those two hosts with the reason and the run in a comment,
  and lists lychee's default globs explicitly, because setting `args` replaces them. The two
  links themselves were not rewritten, since the new targets could not be confirmed
  automatically.

- **The starter kit failed in any repo whose skills had other names.** `--selftest` mutated
  this repo's three skills by path, so a fresh repo with one skill of its own crashed with
  FileNotFoundError, and the starter workflow ran `evals/cli/run.py`, which tests this repo's
  CLI and reported 148 failures there. The selftest now mutates whichever skill sorts first,
  adds a twin of it to test a collision in a one-skill repo, clears a folded description's
  indented lines, and fails by name when a mutation cannot apply. The starter copies only
  `run.py` and no longer runs the CLI test. The same pass added a pinned lychee link check to
  this repo's gate, since nothing checked a link; two context-steward rules (absolute dates,
  and the transcript path to a fresh reviewer after compaction); repo-triage's rule to record
  every verdict, including no, in the same turn; and the American spelling of license.

- **The README's only install command tracked `main` (#36).** A skill is instructions, so an
  install by repository name let a later push change what an agent does with no review on the
  user's machine. The README now leads with a pinned install: clone, check out the commit you
  reviewed, and run the installer on the local copy. The first draft said a `--copy` flag was
  needed to avoid a symlink into the clone; an independent review in throwaway homes showed the
  installer copies anyway, so the claim and the flag were removed before merge.

- **The timeline merged before its review fixes, with a crash that emptied its output file.**
  A lone UTF-16 surrogate in a ledger field, which JavaScript writes whenever it clips a
  string mid-emoji, raised an error after `-o` was opened and left the previous page at 0
  bytes. Ledger text is now cleaned when read, and the page is encoded before `-o` is
  opened, so nothing in a ledger can cost the previous page. `-o` is still written in place,
  as before. A temp file renamed over the target was tried, and two reviews in a row found it
  changing what the plain write did, from `-o /dev/null` and FIFOs to a file's group, so it
  was removed. A disk that fills partway through the write still leaves a partial file, and
  `cannot write` now says why, such as "No space left on device". The same pass stopped the
  page and its tables scrolling sideways at 390 px, bidi controls reversing the page's own
  words, a mistyped kind reading as "the human was not needed", and a 1 MB ledger giving a
  52 MB page. Bare CR line ends are now read as `hsi record` reads them, and a year below
  1000 prints with four digits. Each fix has an eval that failed first.

- **Nothing showed where the operator was needed over a run, or how long each question
  waited.** The ledger held every answer as a line, and recorded neither who asked nor when.
  `hsi timeline LEDGER -o OUT.html` now draws it as one self-contained page, reads four
  optional answer fields (`actor`, `asked_at`, `at`, `evidence`), and says "not recorded"
  when they are absent. It skips and counts malformed lines where `hsi record` stops, and
  says whether `hsi record` would accept the file. The failure list was written first, and a
  mutation pass still found a hole in it: no injection payload put a quote inside an
  attribute, so unescaped quotes passed every injection check until one did.

- **A worker's verdict could reach the operator dressed as a finding.** Four delete verdicts
  from a ranked fan-out of agents were relayed to an operator and approved; three were false
  when checked at the start of the work. `references/honesty-protocol.md` now labels an
  unchecked worker verdict an assumption and asks for a second agent that re-derives each claim
  from the source. The same week showed that checker can go either way: one run confirmed
  every claim against primary sources, and another found half the claims in a tracker wrong.
- **Nothing said where an action goes when the permission layer refuses it.** Two agents hit
  the same boundary on one day from opposite sides: one proposed asking a peer to set a status
  its own gate refused and retracted it within the hour; the other had a write blocked, and the
  right outcome was the person doing it. The SKILL now files a refused action as APPROVE, and
  `AGENTS.md` says it goes to the person, never to another agent.
- **A message queued for session start was reported as received by a session that never
  restarts.** In one setup this happened three times in a month, once for four days.
  `docs/building-a-harness.md` now says to send live what changes the next hour, queue the
  record, do both when it is load-bearing, and check the agent was told before saying it is
  working.
- **The tools matrix said Codex had no known traps because nobody had looked.** The CLI
  accepted an effort level that the API refused for the same models on the same day.
  `docs/tools.md` now records both results and the rule that follows: test a setting on the
  path the harness calls.
- **The operator channel page said `stale` outranks proposals, and described landed work as
  future.** `references/l0-channel.md` and its wiki mirror said `signal` would arrive "once #4
  lands" and that stale beats proposal; `bin/hsi` has ranked stale among the proposals, with 20
  points, since 2026-09-24. Both now match the code, and `docs/building-a-harness.md` no longer
  calls the ledger (#3) and adapter (#7) open.

- **A settled answer could be asked again, and a stale one could rule forever (#3, #4, #7).**
  The skill promised that nothing gets asked twice, but had no file to remember the answer.
  The append-only ledger now requires the operator's words and reasoning, records manual
  invalidation with evidence, and feeds invalidated standing answers to the board through
  the ledger adapter. `stale` adds a printed 20 points and ranks with proposals after errors.
  Neither the ledger nor its adapter detects that a condition fired; a person or agent must
  record the invalidation. An answer carrying a stray top-level `invalidated` key is refused
  before the write, because one such row made the whole append-only file unreadable in review.
- **A per-token price comparison hid the long-context surcharges.** OpenAI and xAI charge more above
  a context threshold and Anthropic does not, which reverses the ranking for a coordinator that
  carries a 500k-token window. `docs/building-a-harness.md` now shows the three rates, read from
  the vendors' pages on 2026-09-24.
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
  scored silently as a proposal; `null` means no signal. `stale` was held until the ledger (#3)
  could produce it. A later owner decision (#1) put direct-evidence errors ahead of proposals.
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
  you measured. Cheapest kill first: license, then maturity, then whether the runtime
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
