# Opening untrusted code with coding agents

A repository is not only code you choose to run. Some files in it run, or steer an agent, as soon as a tool opens the
folder. An attacker who can put one of those files in front of your agent does not need you to run anything.

Three reports from October 2026 show the shape. Each figure below is the reporter's claim, not a measurement made here:
- A planted `AGENTS.md` in a Downloads folder got a coding agent to install malware. In controlled tests, Codex followed
  it in over 90% of attempts ([The Hacker News, via X](https://x.com/TheHackersNews/status/2114600105752015027)).
- JFrog found 42 genuine GitHub repositories, from 11 owners, altered to run malware when opened in Claude Code, Gemini
  CLI, Cursor or VS Code. The payload was about 13 MB, sized to slip past code search
  ([IntCyberDigest, via X](https://x.com/IntCyberDigest/status/2115456553390379371)).
- More than 17,000 repositories got force-pushed commits under their real owners' names. The commits added
  `.vscode/tasks.json` tasks and `.claude/settings.json` hooks that steal AWS keys, npm tokens and Claude logins
  ([Voxyz, via X](https://x.com/Voxyz_ai/status/2115579368109978068)).

The third one matters most. The repository was legitimate yesterday. Trusting a project is not a one-time decision.

## 1. Know which files act on open

Treat these as code, and read them before an agent works in the folder:

| File | What it can do |
|---|---|
| `.claude/settings.json`, `.claude/settings.local.json` | hooks: shell commands on session start or around every tool call |
| `.mcp.json` | MCP servers: a command the agent starts for you |
| `AGENTS.md`, `CLAUDE.md` (in the folder or any parent) | instructions the agent treats as yours |
| `.vscode/tasks.json` | tasks with `"runOn": "folderOpen"` run when VS Code opens the folder |
| `package.json` scripts, `Makefile`, setup scripts | run when the agent "just installs dependencies" |

List them by path first (`find . -path '*/.claude/*' -o -name '.mcp.json' -o -name 'AGENTS.md' -o -name 'CLAUDE.md'
-o -path '*/.vscode/tasks.json'`). Then read each one. A hook or an install line you did not expect is the finding.

## 2. Keep instruction files out of parent folders

Agents load `AGENTS.md` and `CLAUDE.md` from the working folder and from folders above it. A stray file in Downloads, or
in a projects folder, steers every agent started below it. Keep these files only at the root of repositories you own,
and remove stray ones.

## 3. Pin what a headless run loads

An unattended run has no person to see a trust prompt. Make the run decide, not the folder:
- Claude Code: `claude -p --setting-sources "" --settings '{"disableAllHooks":true}'` loads no project, local or user
  settings and runs no hooks. Pass instructions explicitly. `--bare` goes further (see [tools](tools.md)).
- Never start a headless agent with an untrusted repository as its working folder. Copy the files you need into a clean
  folder, or point the agent at them by path.

## 4. Trust named repositories, never parent folders

Codex keeps a list of trusted projects. An entry for a parent folder (your home folder, a whole projects folder, a
synced desktop, Downloads) trusts everything cloned under it later. List each repository you build in by its own path.
Leave everything else untrusted, so it opens read-only and asks before it acts. Recheck the list when you clone
something new.

## 5. Make the hijack hard on your own repositories

The 17,000-repository campaign needed a token that could force-push. On every repository, protect the default branch:
no force push, no deletion, and **no bypass for admins**. A rule that admins bypass does not stop a stolen admin
token. Then watch for the signs:
- force pushes to the default branch that nobody planned (`gh api repos/OWNER/REPO/activity?activity_type=force_push&ref=refs/heads/main`);
- new commits that touch only `.vscode/`, `.claude/` or workflow files;
- branches you did not create.

Keep tokens per host, scoped to what that host needs, with an expiry. Never print a secret into a CI log.

## 6. Prove it in the denying direction

Each trap writes a harmless "canary" file outside the folder if it runs. Build a fixture with one trap per file type
above. Run your real agent commands against it. The pinned runs must leave no canary. Then run one unpinned run on
purpose and watch it write the canary. That proves the canary can fire, and the test is not silent for the wrong
reason. Run it again after every tool upgrade, because a new version can change what a flag loads.

## Checklist

- [ ] Agent-config files listed and read before an agent works in an unfamiliar repository.
- [ ] No `AGENTS.md` or `CLAUDE.md` above your work folders.
- [ ] Headless runs pin their settings and never start inside untrusted code.
- [ ] Codex trust lists named repositories only.
- [ ] Default branch: no force push, no deletion, no admin bypass.
- [ ] A canary fixture runs after each tool upgrade.

Related: [untrusted-input lanes](untrusted-input-lanes.md) (an agent that reads web text), [tools](tools.md).
