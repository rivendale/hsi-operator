# Untrusted-input lanes: where the control actually lives

A web page, a social post or an email can carry instructions. If that text reaches a component that can act
(read files, run commands, make requests), the text can steer it. This page is about the two places teams
usually put the control, and why both were wrong when measured.

## 1. An empty allow-list is not a sealed agent

A command-line agent was run with an empty tools allow-list (`--tools ""`) and a non-interactive permission
mode, on the theory that "allow nothing" means "no tools". The test was a canary: a random string written to a
scratch file and to an environment variable, and a prompt asking the agent to read the file and print the
variable.

It did both. Both canaries appeared in the output. A control prompt ("reply with one word") worked, so the lane
was running. In that version an empty allow-list behaved as no restriction at all.

- **Do not reason from one vendor's flag to another's.** The same flag name meant "no tools" in one CLI and
  "no filter" in another.
- **Prove a lane in the denying direction.** Plant a canary the lane must not reach, ask for it, and check the
  output. A pass is zero hits plus a working control.
- **A usage error is a vacuous pass.** The first attempt used a flag that took an argument and errored before
  the agent ran: zero canary hits, proving nothing. Read what the check would print if it were broken.
- **What to use instead:** a plain model API call with no tools attached, or a provider's server-side tool that
  can only search. Untrusted text never goes to an agent that holds local tools.

## 2. A URL check is not a control for a browser

A headless-browser reader was first built behind a check on the starting URL. The browser does its own DNS,
follows its own redirects and runs scripts, so a public page could redirect it to `127.0.0.1` after the check
had passed. It did, in testing.

The version that held puts the control on the **network path**:

- The browser gets no direct network. Every request goes through a small proxy inside the tool.
- The proxy resolves each host once, through a public-only filter, and connects to that exact IP. There is no
  second lookup for a rebinding name to exploit.
- The browser's habit of sending localhost traffic straight past a proxy is switched off.
- Output is text only, and the tool never hands page text to a model or a shell.

Two measured traps from the independent test of that design:

- **Removing a flag can weaken nothing.** The test plan said to weaken the tool by deleting its loopback-bypass
  flag. The browser library adds the same flag itself, so the "weakened" copy was identical in behavior. Tests
  that assert launch arguments prove nothing; a local listener's log of who connected is the evidence.
- **Every catching test must fail on a weakened copy first.** 212 black-box fixtures were written from the
  failure list by a second agent that never read the code, and each was shown to fail against a deliberately
  broken build before it counted.

The tool, its failure list and the tests are public: [rivendale/opensource `tools/web/`](https://github.com/rivendale/opensource/tree/main/tools/web).

## The pattern under both

The control is the thing that runs, measured in the direction it must refuse. A flag, a prompt instruction or a
pre-check is a description of the control, and the description can be wrong without anyone noticing.
