# Method: building a system map, step by step

The order matters. Triggers come before components because they are what a person asks
about, and deploy truth comes before code because code that does not run is not part of
the system. Every step ends in something you can count.

## 0. Before reading anything

Write five lines and show them to the operator:

1. **The question** the map answers, or "orientation" if there is none yet. A trace answers
   one question; a full map answers "what is this, and what is it doing".
2. **The scope class:** trace, system, or system of systems (see `SKILL.md`).
3. **Sources:** each repo with its commit (`git -C DIR rev-parse --short HEAD`), and the live
   surfaces you may probe, each with the read-only command you will use.
4. **May not touch:** secret files, production writes, user records, any repo or host
   outside scope. Write the list down; a lane without one drifts.
5. **The reader and the moment:** who opens the map, and when.

Then find the **setpoints**: hsi-operator setpoint files, acceptance criteria, or, for a
running system with none, the operator's own sentence for each of the three to five
triggers they care about. Intent comes from a person, never from the code being measured.

Work from a fresh clone at a stated commit. Read with bounded commands: list files and count
matches first (`grep -rlE`, `grep -c`), then read the specific lines. Never pull a whole
large file or log into context.

## 1. Deploy truth

What actually runs, and how it starts. Read these before any application code:

| what | where to look |
|---|---|
| containers and processes | `docker-compose*.yml`, `compose.yaml`, `Procfile`, `Dockerfile` `CMD`/`ENTRYPOINT`, Kubernetes `Deployment`/`StatefulSet`/`DaemonSet` |
| platforms | `fly.toml` (`[processes]`, `[[services]]`), `render.yaml`, `vercel.json`, `netlify.toml`, `wrangler.toml`, `app.yaml`, `serverless.yml`, SAM or CDK stacks, Terraform |
| hosts | systemd `.service` and `.timer` units, launchd plists, Windows services and scheduled tasks, crontabs |
| ingress | nginx `server`/`location`, Caddyfile, Traefik labels, load balancer rules, tunnels, DNS records |
| pipelines | CI workflow files: what deploys, what runs on a schedule |

Each deployable becomes a **level-1 node**. Anything that runs but is in no repo you can
read becomes a node with status `unknown` and a gap. **When the deploy config and the code
disagree, the deploy wins** and the disagreement is a gap.

Live checks at this step are reads: a health endpoint, a platform's status or list command,
`systemctl list-timers`, a container list, a metric query. Record each as
`live YYYY-MM-DD: what was run: what it showed`, with counts, never contents.

## 2. Triggers: every way something starts

Search for each kind, count the hits, and keep an inventory: found, mapped, excluded with a
reason. **The three numbers must add up.**

### User actions
- **Web servers:** Express, Koa, Fastify, Hono (`app.get(`, `router.post(`); Next.js
  (`app/**/route.ts`, `pages/api/**`, server actions marked `'use server'`); Remix,
  SvelteKit, Nuxt (loaders, actions, `+server.ts`, `server/api/`); Django (`urls.py`,
  `path(`); Flask (`@app.route`); FastAPI (`@app.get`, `APIRouter`); Rails
  (`config/routes.rb`); Laravel (`routes/*.php`); Spring (`@GetMapping`, `@PostMapping`);
  ASP.NET (`MapGet`, `[HttpPost]`); Go (`http.HandleFunc`, chi, gin, echo routers); Phoenix
  (`router.ex`).
- **Clients:** pages in the client router are what people see (the read models); calls out
  of the client (`fetch(`, `axios.`, `useMutation`, form `action=`) are what people do.
- **Command lines:** each subcommand of `argparse`, `click`, `typer`, `commander`, `yargs`,
  `cobra`, `clap` is a user action.
- **Chat and bots:** `bot.on(`, `bot.command(`, `app.command(`, slash command registries,
  interaction handlers.

### Webhooks
Routes named `webhook`, `hook`, `callback`, `notify`, `events`, `ipn`, and signature checks,
which are the most reliable marker: `constructEvent`, `svix`, `X-Hub-Signature-256`,
`X-Signature`, `hmac.compare_digest`, `timingSafeEqual`. The registration usually lives in
the provider's dashboard, not the repo: cite the handler, and record a live read of the
provider's endpoint list if you may see it. A handler with no registration found is
`unknown`, not `live`.

### Schedules
`crontab` lines, `node-cron` and `cron.schedule(`, `setInterval` in a long-running server,
APScheduler, Celery beat (`beat_schedule`), Sidekiq-cron, Quartz, Spring `@Scheduled`,
Kubernetes `CronJob`, systemd `OnCalendar=`, CI `on: schedule`, `crons` in `vercel.json`,
`triggers.crons` in `wrangler.toml`, EventBridge rules, scheduled machines on a platform.
Also check how schedules are switched off: an environment flag or a config list. **A
schedule enabled by default with an off switch nobody has used is worth a line in the
map.**

### Queues and internal events
Consumers are triggers; producers are edges. BullMQ (`new Worker(`, `.process(`), Celery
(`@shared_task`, `@app.task`), Sidekiq (`perform`), RQ, SQS (`ReceiveMessage`), Pub/Sub
subscriptions, Kafka (`subscribe(`), NATS, Redis pub/sub, Postgres `LISTEN`/`NOTIFY`,
database triggers, outbox tables, in-process emitters (`.on(` with `emit(`).

### Inbound email and messages
MX records pointing at a provider, inbound parse webhooks, IMAP polling (`imaplib`,
`imapflow`), mail API watch or history polling, SMS and voice callbacks.

### Agents and MCP tools
Tool registries (`server.tool(`, `registerTool(`, `@mcp.tool`, `tools/list` handlers), the
scopes or keys each tool needs, and which tools write. An agent with a write tool is a
controller in the system: map what it can change, what tells a person it did, and whether a
person must confirm.

### Outside updates
Pollers of outside APIs, RSS and feed fetchers, file watchers (`chokidar`, `watchdog`,
inotify), sync clients, package or firmware update channels, data imports on arrival.

### Games
- **Input:** `Input.GetKey`, `_input(event)`, `addEventListener('keydown'`, gamepad polling.
- **The tick:** `Update()`, `FixedUpdate()`, `_process(delta)`, `requestAnimationFrame`, a
  server's fixed tick. The tick is a `schedule` trigger; state machines are components.
- **Network:** RPC handlers, `socket.on(`, message type switches, matchmaking, lobby and
  session services.
- **Persistence and economy:** save and load, inventories, currencies. Map every source
  (where currency or items enter) and every sink (where they leave); that pair is a loop.

### Operating systems and platforms
Boot order (init, systemd targets, launchd), services and their dependencies, device events
(udev rules, hotplug), IPC (D-Bus, sockets, named pipes), the shell and GUI actions people
take, scheduled maintenance, and update channels as `external_update`. Do not map system
calls; map what a person or a device causes to happen.

### Infrastructure
Alert rules (Prometheus rules, uptime checks, log alerts) are triggers of the monitoring
loop: name the condition, where the alert goes, and who sees it. An alert routed nowhere is
a gap.

## 3. Components and stores

Inside each deployable, add a level-2 node only for a part that owns a trigger, touches a
store, or calls out. Everything else stays inside its parent.

Stores come from migrations and schema files, ORM models, bucket names, cache keys, search
indexes, files written to disk, and browser storage. For each table or bucket group, grep
its name in writes (`insert`, `update`, `upsert`, `put`, `.save(`) and in reads (`select`,
`get`, `find`) and record who does which. **A store that is written and never read is an
output without a reader; a store that is read and never written is fed from somewhere you
have not found.**

Outbound calls: HTTP clients and SDK constructors. Take **names** of environment variables
from the code that reads them, or from `.env.example`. Never open a real `.env` file, a key
file, or a credential store.

## 4. Flows

Walk each trigger, one edge at a time, until it reaches an outcome a person or a store can
observe. For each edge write a verb phrase as `label` and the payload in architecture terms
as `data`. When time passes inside a trigger (a job picks it up later, a person comes
back), say so in the narration: the checker warns when a step starts at a node no earlier
step reached, and the narration is where you answer it.

**A cross-repo edge cites both ends:** the call in the producer and the handler in the
consumer. One end alone is a gap.

## 5. Human touchpoints: the HSI layer

For every node, fill `human_sees`: what a person sees or touches there, or `""`. For every
trigger, fill `human_feedback`: what the person sees afterwards, how soon, and through
which channel, or `none` with the reason.

Then read the map as a control structure (from STPA). Controllers, human or automated, issue
**control actions** downward and receive **feedback** upward; each acts on its own picture
of the process, which for a person is whatever their screen shows. Check each controller
against the four ways control goes wrong:

1. **A needed action is not provided:** a failure nobody is told about; an alert with no
   route.
2. **An action is provided that causes harm:** an automatic delete, an agent write with no
   confirmation.
3. **The right action at the wrong time or in the wrong order:** a job that runs before its
   input arrives; a notice sent after the window to act has closed.
4. **An action stopped too soon or applied too long:** retry forever; a sync that gives up
   silently.

Flag every control action with **no feedback path**, and every loop whose feedback is
**slower than the action it governs**. These are where a system drifts while every screen
looks fine.

## 6. Loops: finding them, typing them, judging them

### Finding them
For every store, queue and person on the map, ask: does anything downstream of this write
back into something upstream of it? Common places:

| pattern | type | what to measure |
|---|---|---|
| a worker draining a queue | balancing | queue depth over days: does it return to its floor? |
| retries that re-enqueue on failure | reinforcing | retry rate against error rate under load; is there a cap and backoff? |
| rate limits, quotas, budgets | balancing | how often the limit engages; spend against the cap |
| autoscaling | balancing, can oscillate | replica count over a day; does it flap? |
| producers whose output feeds other producers | reinforcing | machine runs against human reads, over time |
| alerts that a person must act on | balancing while read; reinforcing once ignored (alert fatigue) | alerts per week, time to acknowledge |
| recommendations that shape the behavior they learn from | reinforcing | diversity of what is shown over time |
| caches that refill on a miss | reinforcing at expiry (stampede) | origin load at expiry times |
| a game economy | reinforcing sources, balancing sinks | currency in circulation over time |
| matchmaking ratings | balancing | rating spread and convergence |
| monitoring, then a person, then a fix | balancing | time from failure to a person knowing |

### Typing them
Write each hop as a signed link: `+` when more of `from` gives more of `to`, `-` when more
gives less. Mark `delay: true` where the effect lags. **An odd number of `-` links makes the
loop balancing; an even number makes it reinforcing.** Put the links in the model;
`sysmap check` computes the type from them and refuses a type that disagrees.

### Judging stability
Stability is a judgment, and it needs a measurement behind it.

A **balancing** loop is `stable` when it has a target, something that measures against it,
something with the authority to act, and feedback faster than the disturbance, and a
measurement shows it returning to the target. It is `watch` when the target is implicit, the
sensor is a person who may not look, the delay is long compared with how fast things
change, or the actuator exists and has never been used. It is `unstable` when the sensor or
the actuator is missing or broken, or it oscillates (alerts that flap, scaling that
thrashes).

A **reinforcing** loop is `stable` only when a limit bounds it (a cap, a quota, a budget, a
backoff with a maximum) and the limit has been seen to engage. It is `watch` when the limit
exists but is untested, or growth is measured and slow. It is `unstable` when growth is
measured and nothing bounds it.

**Unmeasured is `watch`**, with "unmeasured" in `why`. `sysmap check` warns about any loop
called `stable` or `unstable` without a `live` evidence line. Good measurements are trends
over time: a ratio of machine output to human reads, queue depth, retry rate, spend, and the
last time a brake was actually used.

## 7. Data uses

For each important piece of data, list who produces it, who reads it, and in `could_serve`
the workflows that would benefit and do not get it today. This is where integration ideas
come from, and they stay ideas: the operator decides which, if any, to build.

## 8. Drift

Write the setpoints into the model's `setpoints` section first: what done means for each
trigger or part that matters, with `holds` judged against the map (`yes`, `no`, or `unknown`
when nothing measured it) and `why`. The operator's own words are `confirmed`; anything taken
from a document or decision is `proposed` until they confirm it.

Then put the setpoints beside the map and give every gap a `kind`:

- `unintended`: running, and no setpoint asks for it, or it works against one.
- `missing`: a setpoint asks for it, and it is absent or broken. Give the `setpoint` id.
- `runaway`: a loop moving away from a target a setpoint names.
- `unknown`: worth knowing, but nobody can say whether it was meant. Not drift.

Then run `sysmap items system-model.json > drift-items.json`. Each drift gap, each setpoint
that does not hold or is unmeasured and that no drift gap carries, and each `unstable` loop
becomes a DECIDE item, with `signal: error` only where a confirmed setpoint failed. Before they
reach Door 1, add 2 to 4 options with consequences, and remove any whose answer does not
depend on the operator. A broken citation or a missing edge is your work, not their question.

## 9. Check, render, second reader

```
sysmap check system-model.json --src owner/repo=PATH   # repeat --src per repo
sysmap render system-model.json -o system-map.html
sysmap items system-model.json > drift-items.json && hsi drift-items.json
```

`check` must exit 0. Read its warnings: each is a place the map is weaker than it looks.
Then hand the model, the setpoints and the repos (not your conclusions) to a second agent
that did not build it, and have it re-measure every `unstable` loop, every `dead` node and
every drift item. Keep what it confirms, downgrade what it cannot reproduce, and say which
was which.

Write the reading note last: one sentence on what the system does, its parts in plain
words, and the five things worth knowing. Open the rendered map on a phone before handing
it over.

## 10. Keeping it current

- Save each model with its date. `sysmap diff old.json new.json` lists what left first.
- Re-map when a condition fires, not on a timer: a new entry point, a new deployable, a
  migration, a new outside service, a moved `watch` measurement, or a setpoint changing.
- When a drift item is answered, the answer goes in the hsi-operator ledger with the
  operator's words and reasoning, so the next map does not ask it again.
- If the map has not been opened in two weeks, report that rather than adding to it.
