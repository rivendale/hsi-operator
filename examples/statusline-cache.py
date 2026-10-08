#!/usr/bin/env python3
"""Claude Code status line: show how long the prompt cache stays warm.

Reads the status line JSON on stdin and prints one line, for example
"cache warm 1h, 42m left, hit 91%, cold rewrite 45k". Uses the `prompt_cache`
object (Claude Code 2.1.251 or later), and prints "cache: no data yet" before the
first response or on an older version. Standard library only.

Settings: {"statusLine": {"type": "command", "command": "python3 /path/to/statusline-cache.py"}}
The minutes count down only when the line re-runs; set the status line's
refreshInterval if you want a live countdown.
"""
import json
import sys
import time

try:
    data = json.load(sys.stdin)
except ValueError:
    data = {}
pc = data.get("prompt_cache") or {}

if not pc:
    print("cache: no data yet")
elif not pc.get("warm"):
    cold = pc.get("recache_tokens_if_cold")
    print("cache COLD" + (f", next turn rewrites {cold // 1000}k" if cold else ""))
else:
    left = max(0, int((pc.get("expires_at") or 0) - time.time()))
    parts = [f"cache warm {pc.get('ttl', '?')}", f"{left // 60}m left"]
    if pc.get("hit_ratio") is not None:
        parts.append(f"hit {pc['hit_ratio']:.0%}")
    if pc.get("misses"):
        parts.append(f"misses {pc['misses']}")
    if pc.get("recache_tokens_if_cold"):
        parts.append(f"cold rewrite {pc['recache_tokens_if_cold'] // 1000}k")
    print(", ".join(parts))
