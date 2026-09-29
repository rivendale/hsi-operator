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
