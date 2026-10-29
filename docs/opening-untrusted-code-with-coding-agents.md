# Opening untrusted code with coding agents

A repository is not only code you choose to run. Some files in it run, or steer an agent, as soon as a tool opens the
folder. An attacker who can put one of those files in front of your agent does not need you to run anything.

Three reports from October 2026 show the shape. Each figure below is the reporter's claim, not a measurement made here:
- A planted `AGENTS.md` in a Downloads folder got a coding agent to install malware. In controlled tests, Codex followed
  it in over 90% of attempts ([The Hacker News, via X](https://x.com/TheHackersNews/status/2114600105752015027)).
- JFrog Security Research found 42 armed third-party GitHub repositories from 11 legitimate owners. They carry execution
  hooks for AI coding assistants and IDEs, plus 12.9-13.7 MB wrappers too large for GitHub code search to return
  ([JFrog, "Beyond testmetest"](https://research.jfrog.com/post/beyond-testmetest-42-hijacked-github-repos/)).
- More than 17,000 repositories got force-pushed commits under their real owners' names. The commits added
  `.vscode/tasks.json` tasks and `.claude/settings.json` hooks that steal AWS keys, npm tokens and Claude logins
  ([Voxyz, via X](https://x.com/Voxyz_ai/status/2115579368109978068)).

The third one matters most. The repository was legitimate yesterday. Trusting a project is not a one-time decision.

## 1. Know which files act on open

Treat these as code, and read them before an agent or editor works in the folder:

| File | What it can do |
|---|---|
| `.claude/settings.json`, `.claude/settings.local.json` | Claude Code hooks: shell commands on session start or around every tool call |
| `.mcp.json`, `.cursor/mcp.json` | MCP servers: a command the agent starts for you |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/` | instructions the agent treats as yours (for parent folders, see section 2) |
| `.gemini/settings.json` | Gemini CLI settings, including its tool and MCP configuration |
| `.vscode/tasks.json` | a task with `"runOptions": {"runOn": "folderOpen"}` can run when VS Code opens the folder, if the folder is trusted and automatic tasks are allowed ([tasks](https://code.visualstudio.com/docs/editor/tasks), [workspace trust](https://code.visualstudio.com/docs/editor/workspace-trust)) |
| `.devcontainer/devcontainer.json` | `initializeCommand` runs on the host machine before the container is built ([reference](https://containers.dev/implementors/json_reference/)) |
| `package.json` scripts, `Makefile`, setup scripts | run when the agent "just installs dependencies" |

List them by path first:

```sh
find . \( -path '*/.claude/*' -o -name '.mcp.json' -o -path '*/.cursor/*' -o -path '*/.gemini/*' \
  -o -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -name 'GEMINI.md' \
  -o -path '*/.vscode/tasks.json' -o -path '*/.devcontainer/devcontainer.json' \) -print
```

Then read each one. A hook, a server command or an install line you did not expect is the finding.

## 2. Keep instruction files out of parent folders

Tools differ in how far up they look, so check each one you use:
- Claude Code loads `CLAUDE.md` from the working folder and from every folder above it. A stray `CLAUDE.md` in
  Downloads, or in a projects folder, steers every Claude Code session started below it.
  [Claude Code docs](https://code.claude.com/docs/en/memory#how-claude-md-files-load).
- Codex reads `AGENTS.md` from the project root (the Git root) down to the working folder, not above that root. A stray
  `AGENTS.md` in Downloads steers Codex when Downloads itself is the project, as when Codex is started there.
  [Codex docs](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Keep these files only at the root of repositories you own, and remove stray ones.

## 3. Pin what a headless run loads

An unattended run has no person to see a trust prompt. Make the run decide, not the folder. For Claude Code (flags as
listed by `claude --help`, version 2.1.312, 2026-10-29):
- `--setting-sources ""` loads no user, project or local settings files. `--settings '{"disableAllHooks":true}'` turns
  off hooks. `--strict-mcp-config` uses only the MCP servers you pass with `--mcp-config`, never the repository's.
- These do **not** stop `CLAUDE.md` discovery, so a repository's `CLAUDE.md` still steers the run. `--bare` skips it,
  along with hooks and plugins (see [tools](tools.md)). Pass instructions explicitly when you use it.
- `--restricted` removes the tools that run commands or code, and WebFetch, unless `--tools` names them. It also ignores
  user, project and local settings files (managed settings and `--settings` still apply). Add `--strict-mcp-config` so
  the repository's MCP servers do not start either. Use it for a run that only needs to read.
- Never start a headless agent with an untrusted repository as its working folder. Copy the files you need into a clean
  folder, or point the agent at them by path.

## 4. Trust named repositories, never broad folders

Codex keeps a list of trusted projects in `~/.codex/config.toml`. Do not add broad entries: your home folder, a whole
projects folder, a synced desktop, Downloads. List each repository you build in by its own path. Whether a parent entry
also covers the folders beneath it depends on the Codex version, so measure it on yours before relying on it either way.
Recheck the list when you clone something new.

## 5. Make the hijack hard on your own repositories

The 17,000-repository campaign needed a token that could force-push. On every repository, protect the default branch:
no force push, no deletion, and no bypass for admins. A rule that admins bypass does not stop a stolen admin token. A
rule with no bypass makes the attacker change the rule first, which needs administration permission and shows in the
audit log. So:
- keep administration permission off the tokens your tools and agents use;
- watch for ruleset and branch-protection changes;
- watch for force pushes to the default branch that nobody planned, with
  `gh api "repos/OWNER/REPO/activity?activity_type=force_push&ref=refs/heads/main"`. Keep the quotes. Unquoted, bash
  sends the call to the background at `&` and drops the branch filter, and zsh treats `?` as a glob;
- watch for new commits that touch only `.vscode/`, `.claude/` or workflow files, and for branches you did not create.

Keep tokens per host, scoped to what that host needs, with an expiry. Never print a secret into a CI log.

## 6. Prove it in the denying direction

Each trap writes a harmless "canary" file outside the folder if it runs. Build a fixture with one trap per file type
above. Run your real agent commands against it. The pinned runs must leave no canary. Then run one unpinned run on
purpose and watch it write the canary. That proves the canary can fire, and the test is not silent for the wrong
reason. Run it again after every tool upgrade, because a new version can change what a flag loads.

## Checklist

- [ ] Agent-config files listed and read before an agent or editor works in an unfamiliar repository.
- [ ] No `AGENTS.md`, `CLAUDE.md` or `GEMINI.md` above your work folders.
- [ ] Headless runs pin their settings, hooks and MCP servers, and never start inside untrusted code.
- [ ] Codex trust lists named repositories only.
- [ ] Default branch: no force push, no deletion, no admin bypass; tool tokens without administration permission.
- [ ] A canary fixture runs after each tool upgrade.

Related: [untrusted-input lanes](untrusted-input-lanes.md) (an agent that reads web text), [tools](tools.md).
