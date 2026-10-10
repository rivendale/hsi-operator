# Writing a brief for another agent

A delegate sees only what you send. Four parts. Send them in this order when the context is long.

1. **Context, above the ask.** Put long documents and inputs first and the request last.
   Anthropic's prompting guide: "Queries at the end can improve response quality by up to 30
   percent in tests, especially with complex, multidocument inputs"
   ([prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices),
   read 2026-09-29). Say what was already tried and failed and what is already known. Give file
   paths, not summaries of files. If the request's authority matters, cite a file the delegate
   can read: an instruction it cannot trace may be refused, and it should be.
2. **Goal, with its limits.** One sentence of what done is, checkable from outside the delegate.
   Then the limits: time, money, which files it may touch, and which model and effort level to use
   ([`choosing-effort.md`](choosing-effort.md)).
3. **Return format, with a stop point.** The shape, the length, and where to stop: "the top 3 with
   evidence, then stop and wait for approval." Ask for references (paths, ids, line numbers), not
   payloads, because whatever a worker returns lands in your context.
4. **Warnings.** Name the irreversible or outward-facing actions it must not take, the data that
   must not leave, and what to do when an action is refused: report it, and do not route around
   it. Give the reason for each rule. The same guide says that explaining why "can help Claude
   better understand your goals and deliver more targeted responses."

A popular template of this shape (goal, return format, warnings, context, from an image widely
shared in September 2026) needs two corrections. When the context is long, it goes above the ask,
not last. And a delegate started fresh, rather than forked from your session, does not know your
codebase or your conversation; it knows the brief.

For a reviewer, the goal is a list of named claims to check, not "is anything wrong?"
([`building-a-harness.md`](building-a-harness.md), item 8).

## The pull request is the reviewer's brief

- **Put the session's decisions on the pull request, not only the diff.** State the intent and
  the acceptance criteria as they were decided, in the decider's words where you have them, and
  the options set aside. A reviewer who sees only the diff can check that the code does what it
  does, not that it does what was wanted.
- **Say exactly what ran, what did not, and claim nothing beyond it.** A public example:
  [gakonst/nanocodex#675](https://github.com/gakonst/nanocodex/pull/675) (Apache-2.0, merged
  2026-09-29) lists the smoke run and the tests that passed, then says the broader suite failed
  one test before the merge, was not rerun after it, and ends: "No claim that the entire suite
  passes." A reader can act on that; "tests pass" gives them nothing to check.
- **A review comment made twice becomes a check.** When the same comment appears on a second pull
  request, turn it into a lint rule, a test or a CI step and prove it on a sample it must reject
  ([`AGENTS.md`](../AGENTS.md), Testing). Reviewers then spend their attention on what a machine
  cannot see.

## What else reaches the delegate

- **The delegate sees the brief and the newest user message, not the conversation.** A
  three-agent workflow launched for a request the person had made several messages earlier
  refused to act: the latest message was an unrelated link, the brief conflicted with it, and a
  search of the repository for the quoted request found nothing. From where the agents stood
  that was correct, because a parent's paraphrase of a request is what a laundered instruction
  looks like. Before launching work for anything but the latest message, write the request
  verbatim into a committed file and cite its path; the re-run with that citation worked.
- **A message sent mid-run can redirect a running delegate.** While the person kept typing,
  one of six researchers returned a report on the person's newest topic instead of its task,
  saying the relayed request "governs". Its one-line summary would have read as done if results
  had been counted rather than read. A line in the brief saying the task is fixed did not hold
  on a later run: five of six agents kept to their task, and the verifier ranked the relayed
  message above the brief and ran nothing. The relay is what the delegate is told to trust, so
  wording cannot outrank it. Check each result against its own brief (the file named, the
  question answered), and run verification when nobody is typing, or outside the fan-out.
- **A handoff is a stronger attack than a request.** In RogueHandoff-20, agents executed harm
  on 0 to 5% of normal tasks and on 40 to 95% after an unsafe trajectory arrived from another
  agent, 5 to 45 points more than the same request made directly
  ([arXiv 2609.18460](https://arxiv.org/abs/2609.18460), read 2026-09-18). The authors say it
  does not establish natural rates or an autonomous cascade; it shows agents readily act on
  unsafe handoffs. Faithful implementation of a plausible artifact from a peer is the failure
  path, and it happens benignly too: one agent implemented a peer's proposed fix exactly as
  specified and reintroduced seven of eight false positives the branch existed to remove. Send
  findings for the recipient to verify, not directives to execute. When a lane is called
  independent, name the channel it could share and check it: delegates that load the same
  instruction file, or read the same repository, inherit the coordinator's frame, and the paper
  found implicit paths between nominally independent evaluation runs. A reviewer with less
  access but a different method is often the more independent one.
- **An agent's account of its own tool is the claim peers check least.** The owner is presumed
  to know, so the description travels as fact. One agent called an alert rule a composite
  "this host is failing" verdict. The rule fired per check and named the failing one. The peer
  said it would never have read the expression, because it had already been told what it was.
  Sending: quote the expression, path or command, not your summary of it. Receiving: treat a
  peer's description of its own tool as believed, not verified, and read the thing before you
  build on it. The same goes for a device: name it by what it reports (a version string, a
  protocol number in a log), not by the story that fits.
- **Relay what the person wants; never relay a permission.** A coordinator may answer a peer's
  question about the person's intent when the person said it or a record shows it. Cite the
  source, and mark "they said" apart from "my read is". Otherwise say "I don't know; I am asking
  them", which stops the peer from guessing too. A wrong fact gets caught by the next
  measurement; a wrong statement of intent steers another agent's work and nothing tests it.
  Permission is a different act. One coordinator told a peer it could land a change "if the diff
  is empty", where the person had told that peer to ask first. The peer refused, correctly: a
  limit the person set moves only when the person moves it. The tell is the verb: *may*, *go
  ahead* or *land it* about something the peer's instructions gate. The mirror case is worse,
  because it sounds like news: "they lifted that limit" should also come from the person, and
  the peer should say so.
