# An overnight read-only audit that someone reads

Written 2026-09-29 from one run, 2026-09-27 into 2026-09-28.

1. **Lanes.** Split by area (hosts, repositories, security, web, records). Every lane is read-only
   and has a written list of what it may not touch.
2. **A verify pass before anyone sees a finding.** A separate agent re-measures every serious
   finding from a different angle and checks it against the written record (decisions, known
   issues, open work). In one run of seven lanes over about 80 minutes, the verify pass tested the
   59 serious findings: 40 confirmed, 15 downgraded and 4 refuted. A worker's verdict is an
   assumption until it is re-derived
   ([honesty protocol](../skills/hsi-operator/references/honesty-protocol.md)).
3. **Severity comes from what the person has to choose**, not from how alarming a finding sounds.
   Red is a decision only they can make; amber is work the owner will do; grey is anything nobody
   can or would act on.
4. **Say what was not checked, grouped by why:** needs admin rights, would have been a write or
   spent money, out of bounds by rule, no instrument, depth limit.
5. **Disclose your own slips** in the report: an instrument that read something it should not
   have, a command that broke a house rule.
6. **Deliver it.** In that run, the main finding was that the existing nightly reports had no
   reader. What was missing was delivery, not more checks
   ([`every-output-needs-a-reader.md`](every-output-needs-a-reader.md)).

## What depth cannot find

More review rounds make code more correct against the input someone assumed. They cannot
find a gap between that assumption and the world.

- **Count the input before hardening the processor.** A chat filter went through 21
  adversarial review rounds and 152 tests before anyone read the live server's logs: twenty
  archives held no chat lines at all, and 16 of 34 join lines carried no name, which the
  parser's pattern rejected, so about half of real joins were silently skipped. Every round had
  read the code and the fixtures, and the fixtures encoded the assumed format. One grep of a
  production log on the first round costs nothing, and its value only falls as work is stacked
  on the assumption. A parser, filter or importer with no measured input is a hypothesis with
  tests.
- **Compare what the user sees, not how it was built.** Two hosts of the same game looked like different
  builds: one served plain HTML and scripts, the other a framework bundle with a tiny shell page. Rendered side by side,
  the body text was identical word for word and the pixels differed by about 1%: a platform had re-wrapped the same game.
  Judging by bundle shape cost a needless decision round. Before calling two hosts different, render both and diff the
  visible text.
- **Verify an export from the receiving end.** An AI build tool reported a project exported to a repository that held no
  commits, while the hosted build stayed live, so the code existed only on the platform. From the exporting side an empty
  export looks finished. Check the receiving repository for an export commit whose date is later than the hosted build's last update.
- **A fallback route must not undo a safety refusal.** A web reader tried a direct fetch, then a headless browser. The direct
  route refused a redirect to a loopback address; the browser route followed it. A fallback that succeeds where the first
  route refused for safety undoes the refusal. Make a safety refusal stop every route, and filter addresses at connect
  time so redirects and DNS rebinding cannot reach private ranges.
- **An audit scan must fetch pull-request refs.** `git fetch --all` does not fetch
  `refs/pull/*`, so a clone can be current on every branch and still lack a commit that exists
  only on an unmerged pull request, while the hosting service still stores it. A secret scanner
  alert said two findings; four different local scans said one, every time, all over the same
  incomplete clone. After `git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'` the
  scan said two. Four methods over one defective input are one measurement, and their agreement
  raised confidence instead of lowering it. When independent methods agree, ask whether they
  shared an input.
- **Diff against the prior version, or a deletion does not exist.** In a versioned set of
  governing documents, a later version silently dropped a clause the earlier one had. Nothing
  in the current version pointed at the gap, so reading it carefully, by a person or a model,
  could not find it. When a "condensed" version appears, diff it and ask what class of thing
  left: protective language is what tends to go. More than one such item is a process finding:
  re-derive from the last good version rather than chase items one at a time.
- **Normalize every timestamp to one clock and one kind of event before reasoning about
  order.** Two verified facts about one service looked mutually exclusive because the timeline
  set local-time commit stamps beside a UTC container-creation time misread as a merge.
  Normalized, the order inverted: the image was built from a branch tip about two minutes
  before that branch merged, and two later merges were never deployed. One cause, not the three
  proposed. When two trusted measurements conflict, suspect the ordering that connects them,
  and settle it by hash or content identity. The remedy has its own trap: a direct check of the
  running artifact aimed at a guessed path returned a confident "absent"; confirm the path
  exists before trusting an absence inside it. A log line stamped with a time and no date gets
  its date from the file or a date line before anyone cites it.
