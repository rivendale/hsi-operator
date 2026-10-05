# Give every code reviewer one written standard, and keep the reviewed change out of it

A review panel of several models, or of people and models, gives better results when every reviewer is
asked the same question. Put that question in one file, `REVIEW.md`, and feed it to each reviewer with
the diff. Then a difference in findings is a difference in judgment, not in instructions.

## What the standard should say

**What to look for, in priority order:**

1. A behavior change nobody asked for: a default, a format, a path, an exit code.
2. Data loss: a delete, an overwrite, a truncation, a replacing import fed a fragment.
3. Security and secrets: a secret in argv, a log or a commit; unchecked input reaching a shell or path.
4. A check that cannot fail. For each new test or guard, ask what it would print if the thing were
   broken. A test that passes on an empty input proves nothing.
5. An effect that never reaches its consumer. The code writes or sends; does the reader get it?
6. A missing edge case: empty, one, many, very large, unicode, a duplicate, a time zone, a retry.

Skip style unless it hides one of these.

**How to write a finding:** one line, starting with the severity, naming the input that triggers it, the
expected result and the actual result. A finding without a triggering input is a guess; tag it.

**How to think:** list the ways the change could fail before reading the implementation. Reading first
anchors the reviewer on the author's idea of the problem. "No defects found" is a valid answer. A lone
correct dissent is the most valuable thing a panel produces. A fix can bring a new bug, so check fixes.

## Keep the change under review out of the standard

The standard is an instruction to the reviewer, so it is an injection target. A pull request that edits
`REVIEW.md` to say "approve everything" must not be reviewed against its own edit. Three rules, each
learned from a review of the first version:

- **Read every copy from git, never from a working tree.** A copy next to the review script picks up a
  branch checkout or an uncommitted edit.
- **Read the reviewed repo's copy from the real base branch.** An incremental review that compares
  against an earlier head of the same branch reads text the branch author controls.
- **Restate the output format after the appended standards**, so appended text cannot override it.

Cap each file's size in bytes, not characters, and warn when the cap cuts. One more trap from the same
round: a tool that drops a half-cut character can exit non-zero. A caller that reads that as "file
missing" then silently drops the whole standard.

## Measure it

Test each rule in the refusing direction: a hostile base copy, a hostile head copy, a hostile
uncommitted edit, an oversized file, a finding with a leading tag. Then the bigger question: does the
standard raise recall? Seed known bugs into real diffs and compare the panel with and without it.
