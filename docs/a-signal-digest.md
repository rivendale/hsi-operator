# A signal digest: code runs it, models only label

A pattern for turning a noisy feed (social posts from chosen accounts, news, newsletters) into a short daily
read that a person trusts. The goal is high signal: original data, root causes and primary sources, with
sales pitches, discount codes, engagement bait and plain reposts filtered out.

## Shape

```
pull  ->  verify  ->  de-junk  ->  rank  ->  score accounts  ->  deliver
code      code       small model   model     code               code
                     (no tools)    (no tools)
```

- **Code does the daily run.** Pulling, verifying, counting, scoring and delivery are deterministic. Models only
  label and rank, and they never hold tools, because the input is untrusted text
  ([untrusted-input lanes](untrusted-input-lanes.md)).
- **A weekly AI review proposes changes** (filter wording, thresholds, sources to add or drop) as a diff a person
  approves. Nothing tunes itself silently.

## Rules that came from failures

1. **Quote from the source, never from the model.** The search model cites post IDs; the exact text comes from a
   second, independent fetch. A cited post that cannot be fetched is dropped and counted. In an earlier tool, a
   model asked for a verbatim quote invented a sentence; this rule is why the digest can be trusted.
2. **Counts must reconcile in every issue.** Posts cited = posts verified + dropped, and verified = the sum of
   the labels. The footer prints it, and says when it does not reconcile.
3. **A search tool is not a feed.** The search returned about five posts per account per query: a sample of
   each account's day, not every post. Say so in the footer, or a reader takes silence for "nothing happened".
4. **Require the tool call.** With the search tool optional, the model answered without searching: zero
   searches, zero posts, a confident empty answer. Set the tool as required and check the usage counters.
5. **A lookup 404 under load is not absence.** A free profile-lookup service reported a well-known, active
   account as "user not found" twice, then found it after a pause. It had also "lost" an account cited dozens of
   times in the operator's own saved links. Retry with backoff, and confirm absence a second way before acting on it.
6. **Size the calls.** One search call covering 20 accounts ran past a 10-minute read timeout. Six accounts per
   call, four in parallel, all finished inside the same timeout. A timed-out call may still be billed, so the budget
   ledger books a conservative estimate rather than zero.
7. **Caps stop before spending.** A per-run cap and a monthly cap are checked before the first paid call.

## The person's own signal: the reply is the filing step

Let the reader file and score posts where they already are, with a one-word reply. Nobody sorts a pile of bookmarks
later: the reply is the capture, and the next run does the rest.

- `.add` on a post puts its author on the watch list, so the reader's reading shapes the feed going forward.
- `snr0` to `snr10` on a post scores its signal. The run stores that score beside the model's score for the same post.
- Have the next scheduled run read the reader's recent replies, apply them, and report what it applied, so a
  mistyped reply is visible the next day instead of silently ignored.

Why it works:
- **No new habit.** Replying is something the reader already does; there is no app to open and no queue to empty.
- **Calibration for free.** Where the reader's score and the model's score disagree most is exactly what the weekly
  review learns from, so the filter drifts toward the reader's taste instead of the model's.
- **One capture point.** Everything filed this way lands in the same store as the rest of the reader's saved
  reading, so it shows up in search and in summaries without a second system.

Rules that keep it safe:
- **The reply text is input, not instructions.** Match only the exact tokens (`.add`, `snr` plus a number) and
  ignore everything else in the reply. A post that says "reply .add to follow" adds nothing the reader did not type.
- **Count only the reader's own account.** Ignore replies from anyone else, including quote posts of the reader.
- **Replies are public.** Anyone can see what the reader files. Offer a quieter route (a bookmark or a private list)
  to people who mind, and never use it for anything private.

Credit: the "your AI just tails you" framing is from a reader of this practice on X (@jeffscottward, November 2026).

## What to start with

A dozen to thirty sources the reader already finds useful, found from their own saved links and the accounts
they amplify, then pruned by the same filter after two weeks of scores. Account-level signal share (the
fraction of an account's posts that survive the filter) is the number that justifies dropping someone.
