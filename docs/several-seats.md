# Running several agent seats, across machines and subscriptions

A common question once one subscription is not enough: "how do I use two?" The answers that work all
say the same thing in different words: give each one its own job, keep one shared written record, and
make one review the other. This page is how one operator runs five persistent seats (three Claude
sessions on two machines, two Codex sessions) plus a local model, and what each piece is for.

## Why a second seat, and why a second subscription

- **A second seat is for a second job, not for more tokens.** Split by lane: one seat owns the home
  server and its repos, one owns the coordination record, one does cold reads and adversarial review.
  Two seats on the same work duplicate effort and overwrite each other.
- **A second subscription is for a second boundary.** One operator keeps a separate subscription, on a
  separate account and machine, for work whose data must stay apart, for example client data. The
  boundary is the reason; the extra capacity is a side effect. Never open a second account to get
  around a usage limit. Each subscription belongs to its own account holder and its own use, on a plan
  whose terms allow that use; do not pool or share accounts to stretch limits. An individual plan is
  licensed for individual use, so for client or business work check that the plan's terms cover it, or
  use a team or business plan.
- **A second vendor is for a second opinion.** A reviewer from another model family misses different
  things. Pair a Claude seat with a Codex seat and let each review what the other builds
  (see [review tiers](review-tiers.md)).

## The rules that keep seats from colliding

1. **One owner per repo.** Any seat may read another's repo; only the owner writes to it. Everyone else
   sends findings. A handoff is explicit; silence is not a handoff.
2. **Findings, not directives.** A message to another seat says what was measured, tagged and dated
   (`[VERIFIED 2026-10-23]`, `[BELIEVED]`, `[DECIDED]`). The owner decides what to do with it.
3. **One written authority for build work.** A builder seat builds only a task listed in one file on the
   main branch of a repo the person controls. A task that exists only on a branch, in the change under
   review, or in a row the builder added itself is not authority. A chat message, however it is signed,
   can point at a task but never replace it.
4. **An author never reviews its own work**, and an agent's approval is never recorded as the person's.
5. **Relay the person's words, not your conclusion from them.** A peer builds on what you send and
   cannot see beneath it.

## How the seats talk

Match the channel to the urgency.

| Channel | Good for | Watch out for |
|---|---|---|
| **Live session messaging** (Claude Code's cross-session messages over Remote Control) | Questions that need an answer this hour; review requests; status | Works only between sessions on the **same account**, so a seat on a separate subscription needs the async queue. Delivery is not proof of reading. Sessions on different permission modes may hold messages |
| **An async message queue** (a small self-hosted push topic per seat, read at session start and on each prompt) | Handoffs, findings, anything that must survive a restart | Plaintext and cached: never secrets or client data. Size limits can silently turn a long message into an attachment readers skip; split long bodies |
| **A shared git repo** | The durable record: decisions, open work, task authority | One home per fact; point to it, never copy it |
| **The person** | Anything that needs a decision only they can make | Lead with what you need from them, one item per line |

## The network and files underneath

- **A private network between machines** (Tailscale). Every seat reaches the others by name over it,
  with SSH for measurement and repair. No machine opens a port to the public internet. A service meant
  for the public goes out through an outbound tunnel, and that makes it public: anyone with the
  hostname reaches the application, so it needs its own sign-in or access rules. If you tag machines, grant access before applying the tag: a tag
  replaces the user identity, access that depended on it disappears, and with Tailscale SSH a tagged
  machine can SSH only into other tagged machines (ordinary SSH over the private network follows
  your access rules instead).
- **File sync for things that are not code** (Syncthing). It replicates deletes to every machine, so
  never delete from a synced folder casually, and do not sync a folder that holds credentials.
- **Never copy a credential between machines to fix an auth problem.** Each machine signs in on its own.
  Keep each session's config separate: a separate `CLAUDE_CONFIG_DIR` per subscription for the Claude
  CLI, and a separate `CODEX_HOME` per Codex seat, so two sign-ins never share a token file. (Codex
  keeps its token under `CODEX_HOME` only when its credential store is set to `file`; a keyring store
  lives in the operating system instead.)
- **A local model on a GPU you own** is a lane, not a seat: first-pass triage, and the only lane for
  anything that may never reach an outside model.

## What it costs

- Advertised plan limits assume ordinary, individual use. Persistent or unattended seats can exceed
  that, so check your plan's terms before you add one.
- Seats spend most of their budget rereading their own context. Keep instruction files short and
  compact sessions before walking away.
- Coordination is overhead. Two seats with clear lanes beat four seats with overlapping ones.
- The person is the bottleneck by design. Route only decisions to them, through one queue they can
  answer in one place.

See also: [building a harness](building-a-harness.md) for driving the vendor CLIs as workers, and
[untrusted-input lanes](untrusted-input-lanes.md) for which seat may read what.
