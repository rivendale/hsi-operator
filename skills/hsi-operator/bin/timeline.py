"""Draw the append-only ledger as a timeline: where the human was needed, and how long
each wait was.

    hsi timeline LEDGER -o OUT.html     one self-contained page; no -o writes it to stdout

The page is inline CSS and SVG with no script, no request and no model, and the same
ledger always gives the same bytes.

WHY A SECOND, LENIENT READ. `read_ledger` stops at the first bad line, because the
commands that use it act on the standing answer and must not act on a guess. A picture of
a run should survive a bad line, skip it, and say how many it skipped. The page still runs
`read_ledger` and says whether `hsi record` would accept the file.

WHAT IT CAN AND CANNOT SEE. A ledger answer has a day, a kind, the question and the
answer. It does not say who asked or when the question was asked, so the page reads four
optional fields and says "not recorded" when they are absent rather than guessing:

  actor     who asked, and so whose lane the point sits in
  asked_at  when the question reached the operator (ISO 8601 date or date-time)
  at        when it was answered, finer than `date`; on an invalidation, inside `invalidated`
  evidence  a link or a reference for the answer

`hsi record` keeps extra fields, so an answer carrying these is still a valid row. A
question still waiting has no ledger line yet, so the page shows answered questions only.

The per-actor lanes, with a kind on every event, are an idea from microsoft/TinyTroupe
(MIT), whose simulations print each agent's stream with its action kind. No code was taken.
"""

import argparse
import datetime
import html
import json
import math
import os
import re
import stat
import sys
import tempfile

from ledger import KINDS, LedgerError, invalid_answer_field, read_ledger, valid_date


INVALIDATED = "invalidated"
OTHER = "other"
CATEGORIES = KINDS + (INVALIDATED, OTHER)
GLYPH = {"DECIDE": "D", "APPROVE": "A", "EXECUTE": "E", "TASTE": "T", OTHER: "?"}
TABLE_GLYPH = {"DECIDE": "◆", "APPROVE": "■", "EXECUTE": "▲", "TASTE": "●",
               INVALIDATED: "×", OTHER: "○"}
SHAPE = {
    "DECIDE": '<polygon class="shape" points="0,-8.5 8.5,0 0,8.5 -8.5,0"/>',
    "APPROVE": '<rect class="shape" x="-7" y="-7" width="14" height="14" rx="2"/>',
    "EXECUTE": '<polygon class="shape" points="0,-8.5 8.5,6.5 -8.5,6.5"/>',
    "TASTE": '<circle class="shape" r="7.5"/>',
    INVALIDATED: '<path class="shape" d="M-5,-5L5,5M-5,5L5,-5"/>',
    OTHER: '<circle class="shape" r="6.5"/>',
}
GLYPH_Y = {"EXECUTE": 4.6}

DEFAULT_LANE = "no actor recorded"
MAX_LANES = 12          # more actors than this merge into one lane that says how many it holds
TABLE_LIMIT = 2000      # event rows in the table; the rest are counted and pointed at
MAX_BARS = 1500         # wait bars drawn, longest first
TEXT_LIMIT = 600        # characters shown from any one ledger field
NAME_LIMIT = 120        # characters shown from an actor or item id, which can repeat on every mark

LABEL_W, CHART_W, AXIS_H, HEAD_H, SUB_H, LANE_GAP, SIDE_W, COL, EDGE = 120, 900, 30, 20, 24, 8, 120, 18, 16

# One explicit pattern, so Python versions that accept different ISO spellings still
# agree on which times are readable.
TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d{3}(\d{3})?)?)?(Z|[+-]\d{2}:\d{2})?")
EPOCH = datetime.datetime(1970, 1, 1)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
SECOND_STEPS = (1, 5, 15, 30, 60, 300, 900, 1800, 3600, 7200, 10800, 21600, 43200,
                86400, 172800, 604800, 1209600)


# A lone UTF-16 surrogate is a valid JSON escape and not valid Unicode: a JavaScript writer
# produces one whenever it clips a string in the middle of an emoji. It cannot be encoded
# as UTF-8, so it is shown as U+FFFD. A pair that JSON joins into one character never
# reaches this pattern.
SURROGATE = re.compile("[\ud800-\udfff]")
# Bidi embeddings, overrides and isolates (U+202A-202E, U+2066-2069). One left open in a
# ledger field reverses the page's own words after it, in HTML and in SVG tooltips alike,
# and can make "gnp.exe" read "exe.png". Removed. Hebrew or Arabic text needs none of them
# to display in its own direction.
BIDI_CONTROL = re.compile("[\u202a-\u202e\u2066-\u2069]")


def clean(text):
    """Ledger text made safe to print."""
    return BIDI_CONTROL.sub("", SURROGATE.sub("\ufffd", text))


def esc(value):
    return html.escape(value, quote=True)


def clip(text, limit=TEXT_LIMIT):
    return text if len(text) <= limit else text[:limit] + "…"


def label(value):
    """Display text for any JSON value: strings as they are, anything else as JSON."""
    if value is None:
        return ""
    if isinstance(value, str):
        return clean(value)
    try:
        return clean(json.dumps(value, ensure_ascii=False)[:TEXT_LIMIT + 1])
    except (ValueError, RecursionError):
        return "(unreadable value)"


def plural(n, word):
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def parse_time(value):
    """(naive UTC datetime, "day" or "time"), or None when the value is not a readable time.

    An offset is converted to UTC and a time with no offset is read as UTC, so two clocks
    cannot manufacture a contradiction, and the page says which rule it used.
    """
    if not isinstance(value, str):
        return None
    if valid_date(value):
        return datetime.datetime.fromisoformat(value), "day"
    if not TIME_RE.fullmatch(value):
        return None
    try:
        moment = datetime.datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
        if moment.tzinfo is not None:
            moment = moment.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    except (ValueError, OverflowError):
        return None
    return moment, "time"


def pick_time(*values):
    """The first readable time among the values given, and the first unreadable one."""
    bad = None
    for value in values:
        if value is None:
            continue
        parsed = parse_time(value)
        if parsed:
            return parsed, bad
        if bad is None:
            bad = value
    return None, bad


def show_time(moment):
    if moment is None:
        return "not recorded"
    when, precision = moment
    if precision == "day":
        return f"{when:%Y-%m-%d} (day only)"
    return f"{when:%Y-%m-%d %H:%M}" + (f":{when:%S}" if when.second else "") + " UTC"


def duration(seconds, approximate=False):
    if approximate:
        days = int(seconds // 86400)
        return "same day" if days == 0 else f"about {plural(days, 'day')}"
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        hours, minutes = divmod(s // 60, 60)
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    days, rest = divmod(s, 86400)
    return f"{days}d {rest // 3600}h" if rest // 3600 else f"{days}d"


def total(waits):
    seconds = sum(w["seconds"] for w in waits)
    text = duration(seconds)
    return ("about " + text) if any(w["approximate"] for w in waits) else text


def is_link(value):
    return isinstance(value, str) and re.fullmatch(r"https?://[^\s<>\"'`]+", value.strip()) is not None


# --- reading ---------------------------------------------------------------------------

def parse_row(raw, number):
    """(reason skipped, row): exactly one of the two is None."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "not UTF-8", None
    if number == 1 and text.startswith("\ufeff"):
        text = text[1:]
    if not text.strip():
        return "blank", None
    try:
        row = json.loads(text)
    except (ValueError, RecursionError):
        return "not JSON", None
    if not isinstance(row, dict):
        return "not a JSON object", None
    return None, row


def text_or_none(value, strip=False):
    """A string field, cleaned, or None when it is not a string or holds nothing to show."""
    if not isinstance(value, str):
        return None
    text = clean(value)
    return (text.strip() if strip else text) if text.strip() else None


def make_event(number, row, lane_of_item):
    item = text_or_none(row.get("item_id"))
    actor = text_or_none(row.get("actor"), strip=True)
    event = {"line": number, "item": item, "notes": [], "question": "", "answer": "", "raw_kind": None,
             "asked": None, "wait": None, "wait_text": "n/a"}
    invalidation = row.get("invalidated")
    if "invalidated" in row and isinstance(invalidation, dict):
        event["category"] = INVALIDATED
        event["lane"] = lane_of_item.get(item) or actor or DEFAULT_LANE
        event["when"], bad = pick_time(invalidation.get("at"), invalidation.get("date"))
        event["evidence"] = evidence_of(invalidation)
    else:
        kind = row.get("kind")
        event["category"] = kind if isinstance(kind, str) and kind in KINDS else OTHER
        event["raw_kind"] = clip(label(kind) or "null", 40) if "kind" in row else None
        event["lane"] = actor or DEFAULT_LANE
        event["when"], bad = pick_time(row.get("at"), row.get("date"))
        event["evidence"] = evidence_of(row)
        event["question"], event["answer"] = label(row.get("question")), label(row.get("answer"))
    if bad is not None:
        event["notes"].append(f"unreadable time {clip(label(bad), 40)!r}")
    if event["category"] in KINDS:
        if item:
            lane_of_item[item] = event["lane"]
        missing = invalid_answer_field(row)
        if missing:
            event["notes"].append(f"not a complete ledger answer: {missing} is missing or invalid")
        reason = row.get("supersedes_reason")
        if isinstance(reason, str) and reason.strip():
            event["notes"].append("replaces an earlier answer: " + clean(reason))
        measure_wait(event, row.get("asked_at"))
    return event


def evidence_of(row):
    value = row.get("evidence")
    return clean(value) if isinstance(value, str) else value


def measure_wait(event, asked_value):
    asked, bad = pick_time(asked_value)
    event["asked"] = asked
    when = event["when"]
    if asked is None:
        event["wait_text"] = "not recorded"
        if bad is not None:
            event["notes"].append(f"unreadable asked_at {clip(label(bad), 40)!r}")
        return
    if when is None:
        event["wait_text"] = "not recorded: no answer time"
        return
    if asked[1] == "time" and when[1] == "time":
        seconds, approximate = (when[0] - asked[0]).total_seconds(), False
    else:
        seconds, approximate = (when[0].date() - asked[0].date()).days * 86400, True
    if seconds < 0:
        event["wait_text"] = "answered before it was asked"
        return
    event["wait"] = {"seconds": seconds, "approximate": approximate}
    event["wait_text"] = duration(seconds, approximate)


def split_lines(raw):
    """One chunk read up to b"\\n", split where `read_ledger` splits it: text mode ends a line
    at "\\n", "\\r\\n" or a bare "\\r", so both readers give a record the same line number."""
    if raw.endswith(b"\r\n"):
        raw = raw[:-2]
    elif raw.endswith(b"\n") or raw.endswith(b"\r"):
        raw = raw[:-1]
    return raw.split(b"\r")


def read_events(path):
    """(events, skipped, lines read). Never raises on content; only on opening the file."""
    events, skipped, lines, lane_of_item = [], [], 0, {}
    with open(path, "rb") as source:
        for raw in source:
            for piece in split_lines(raw):
                lines += 1
                reason, row = parse_row(piece, lines)
                if reason:
                    skipped.append((lines, reason))
                else:
                    events.append(make_event(lines, row, lane_of_item))
    return events, skipped, lines


def strict_verdict(path):
    try:
        read_ledger(path)
    except (LedgerError, ValueError, OSError, RecursionError) as error:
        return f"hsi record would refuse this ledger: {clip(clean(str(error)), 200)}."
    return "hsi record reads this ledger without error."


# --- layout ----------------------------------------------------------------------------

def seconds_of(moment):
    return (moment - EPOCH).total_seconds()


def ticks(t0, t1):
    """At most nine ticks on calendar or clock boundaries, and how to label them."""
    span = (t1 - t0).total_seconds()
    if span <= 0:
        return [t0], "full"
    for step in SECOND_STEPS:
        if span / step <= 8:
            start = math.ceil(seconds_of(t0) / step) * step
            found = []
            while start <= seconds_of(t1) and len(found) < 9:
                found.append(EPOCH + datetime.timedelta(seconds=start))
                start += step
            return found or [t0], ("seconds" if step < 60 else "clock" if step < 86400 else "day")
    for months in (1, 3, 6):
        if span / (months * 30.44 * 86400) <= 8:
            index = t0.year * 12 + t0.month - 1
            index += (-index) % months
            found = []
            while len(found) < 9 and index // 12 <= t1.year:
                moment = datetime.datetime(index // 12, index % 12 + 1, 1)
                if moment > t1:
                    break
                if moment >= t0:
                    found.append(moment)
                index += months
            return found or [t0], "month"
    step = next(m * 10 ** p for p in range(5) for m in (1, 2, 5) if (t1.year - t0.year) / (m * 10 ** p) <= 8)
    year = t0.year + (-t0.year) % step
    found = []
    while year <= t1.year and len(found) < 9:
        if datetime.datetime(year, 1, 1) >= t0:
            found.append(datetime.datetime(year, 1, 1))
        year += step
    return found or [t0], "year"


def tick_label(moment, style, mode):
    if style == "full":
        return f"{moment:%Y-%m-%d %H:%M}" if mode == "clock" else f"{moment:%Y-%m-%d}"
    if style in ("seconds", "clock") and moment.time() == datetime.time():
        return f"{MONTHS[moment.month - 1]} {moment.day}"
    if style == "seconds":
        return f"{moment:%H:%M:%S}"
    if style == "clock":
        return f"{moment:%H:%M}"
    if style == "day":
        return f"{MONTHS[moment.month - 1]} {moment.day}"
    if style == "month":
        return f"{MONTHS[moment.month - 1]} {moment.year}"
    return str(moment.year)


def assign_lanes(events):
    """Lanes in order of first appearance; past MAX_LANES, the smallest merge into one."""
    first, count = {}, {}
    for e in events:
        first.setdefault(e["lane"], len(first))
        count[e["lane"]] = count.get(e["lane"], 0) + 1
    names = sorted(first, key=first.get)
    if len(names) <= MAX_LANES:
        return names, {n: n for n in names}
    keep = set(sorted(names, key=lambda n: (-count[n], first[n]))[:MAX_LANES - 1])
    merged = f"{len(names) - len(keep):,} other actors"
    mapping = {n: (n if n in keep else merged) for n in names}
    return [n for n in names if n in keep] + [merged], mapping


def layout(events):
    lanes, mapping = assign_lanes(events)
    for e in events:
        e["shown_lane"] = mapping[e["lane"]]
    mode = "clock" if any(e["when"] and e["when"][1] == "time" for e in events) else "day"

    def place(moment):
        if moment is None or (moment[1] == "day" and mode == "clock"):
            return None
        return datetime.datetime.combine(moment[0].date(), datetime.time()) if mode == "day" else moment[0]

    for e in events:
        e["t"] = place(e["when"])
        e["t_asked"] = place(e["asked"]) if e["wait"] and e["t"] is not None else None
    points = [e["t"] for e in events if e["t"] is not None] + [e["t_asked"] for e in events if e["t_asked"]]
    side = [e for e in events if e["t"] is None]
    if points:
        x_right = CHART_W - EDGE - (SIDE_W if side else 0)
        side_left = CHART_W - SIDE_W
    else:
        x_right, side_left = EDGE, EDGE
    t0, t1 = (min(points), max(points)) if points else (None, None)

    def x_of(moment):
        if t1 == t0:
            return (EDGE + x_right) / 2
        return EDGE + (moment - t0).total_seconds() / (t1 - t0).total_seconds() * (x_right - EDGE)

    for e in events:
        if e["t"] is not None:
            e["x"] = x_of(e["t"])
            e["x_asked"] = x_of(e["t_asked"]) if e["t_asked"] is not None else None
    width = CHART_W - side_left
    for i, e in enumerate(side):
        e["x"] = side_left + width / 2 if len(side) == 1 else side_left + 14 + i * (width - 28) / (len(side) - 1)
        e["x_asked"] = None

    rows, y, lane_geometry = {}, AXIS_H, []
    for name in lanes:
        present = [c for c in CATEGORIES if any(e["shown_lane"] == name and e["category"] == c for e in events)]
        subs = {c: y + HEAD_H + i * SUB_H + SUB_H / 2 for i, c in enumerate(present)}
        rows[name] = subs
        lane_geometry.append((name, y, subs))
        y += HEAD_H + max(len(present), 1) * SUB_H + LANE_GAP
    return {"lanes": lanes, "rows": rows, "geometry": lane_geometry, "height": y + 4, "mode": mode,
            "t0": t0, "t1": t1, "x_of": x_of if points else None, "side": side, "side_left": side_left,
            "has_axis": bool(points)}


def group_marks(events, geo):
    groups = {}
    for e in events:
        region = "side" if e["t"] is None else "axis"
        key = (e["shown_lane"], e["category"], region, int(e["x"] // COL))
        g = groups.get(key)
        if g is None:
            groups[key] = g = {"events": [], "x": e["x"], "y": geo["rows"][e["shown_lane"]][e["category"]],
                               "category": e["category"], "lane": e["shown_lane"]}
        g["events"].append(e)
    for g in groups.values():
        for e in g["events"]:
            e["group"] = g
    return list(groups.values())


# --- drawing ---------------------------------------------------------------------------

def marker(category, extra=""):
    """One mark centered on its group's origin: a shape per kind, and a letter inside it."""
    glyph = GLYPH.get(category)
    text = f'<text class="glyph" y="{GLYPH_Y.get(category, 3.2)}">{glyph}</text>' if glyph else ""
    return f'<g class="k-{category}">{SHAPE[category]}{text}{extra}</g>'


def describe(e):
    parts = [f"{e['category']} · {clip(e['lane'], NAME_LIMIT)} · line {e['line']}", show_time(e["when"])]
    if e["category"] == INVALIDATED:
        parts.append(f"invalidated {clip(e['item'] or '(no item id)', NAME_LIMIT)}: {clip(label(e['evidence']), 200)}")
    else:
        if e["question"] or e["answer"]:
            parts.append(clip(e["question"], 200) + (" → " + clip(e["answer"], 200) if e["answer"] else ""))
        if e["category"] in KINDS:
            parts.append(f"wait: {e['wait_text']}")
    return "\n".join(parts)


def draw_chart(events, geo, groups, drawable, in_table):
    out = []
    height = geo["height"]
    out.append(f'<svg class="chart" width="{CHART_W}" height="{height}" viewBox="0 0 {CHART_W} {height}" '
               'role="group" aria-label="Timeline chart. Each mark links to its row in the event table below.">')
    for name, top, subs in geo["geometry"]:
        out.append(f'<line class="rule" x1="0" x2="{CHART_W}" y1="{top:.1f}" y2="{top:.1f}"/>')
    if geo["has_axis"]:
        found, style = ticks(geo["t0"], geo["t1"])
        for t in found:
            x = geo["x_of"](t)
            out.append(f'<g class="tick"><line x1="{x:.1f}" x2="{x:.1f}" y1="{AXIS_H - 6}" y2="{height - 4}"/>'
                       f'<text x="{x:.1f}" y="{AXIS_H - 11}">{esc(tick_label(t, style, geo["mode"]))}</text></g>')
    if geo["side"]:
        left = geo["side_left"]
        precisions = {("none" if e["when"] is None else "day") for e in geo["side"]}
        title = {"none": "no time", "day": "day only"}.get(precisions.pop()) if len(precisions) == 1 else "day only or none"
        if left > EDGE:
            out.append(f'<line class="rule" x1="{left}" x2="{left}" y1="0" y2="{height}"/>')
        out.append(f'<text class="side-title" x="{left + (CHART_W - left) / 2:.1f}" y="{AXIS_H - 11}">{esc(title)}</text>')
    for name, top, subs in geo["geometry"]:
        lane_events = [e for e in events if e["shown_lane"] == name]
        human = [e for e in lane_events if e["category"] in KINDS]
        waits = [e["wait"] for e in human if e["wait"]]
        text = f"{plural(len(human), 'human point')}"
        if waits:
            text += f", {total(waits)} of recorded waiting"
        others = len(lane_events) - len(human)
        if others:
            text += f", {plural(others, 'other event')}"
        out.append(f'<text class="lane-sum" x="{EDGE}" y="{top + 14:.1f}">{esc(text)}</text>')

    bars = sorted(drawable, key=lambda e: (-e["wait"]["seconds"], e["line"]))[:MAX_BARS]
    occupied = {}
    for g in groups:
        occupied.setdefault((g["lane"], g["category"]), []).append(g["x"])
    for e in bars:
        y = e["group"]["y"]
        out.append(f'<g class="k-{e["category"]}"><line class="bar" x1="{e["x_asked"]:.1f}" x2="{e["x"]:.1f}" '
                   f'y1="{y:.1f}" y2="{y:.1f}"/><line class="bar-start" x1="{e["x_asked"]:.1f}" '
                   f'x2="{e["x_asked"]:.1f}" y1="{y - 5:.1f}" y2="{y + 5:.1f}"/></g>')
        text = e["wait_text"]
        width = 6.2 * len(text)
        mid = (e["x_asked"] + e["x"]) / 2
        crowded = any(abs(x - mid) < width / 2 + 10 for x in occupied[(e["shown_lane"], e["category"])])
        if len(e["group"]["events"]) == 1 and e["x"] - e["x_asked"] >= width + 26 and not crowded:
            out.append(f'<text class="bar-label" x="{mid:.1f}" y="{y - 7:.1f}">{esc(text)}</text>')

    for g in groups:
        members = g["events"]
        first = members[0]
        if len(members) == 1:
            tip = describe(first)
        else:
            timed = [e["when"] for e in members if e["when"]]
            waits = [e for e in members if e["wait"]]
            tip = f"{len(members):,} {g['category']} events · {clip(g['lane'], NAME_LIMIT)}"
            if timed:
                tip += f"\n{show_time(min(timed))} to {show_time(max(timed))}"
            if waits:
                longest = max(waits, key=lambda e: (e["wait"]["seconds"], -e["line"]))
                tip += f"\nlongest wait {longest['wait_text']} (line {longest['line']})"
            lines = ", ".join(str(e["line"]) for e in members[:8])
            tip += f"\nlines {lines}" + (", …" if len(members) > 8 else "")
        count = f"×{len(members):,}"
        right = g["x"] + 10 + 6 * len(count) <= CHART_W
        place = 'x="10"' if right else 'x="-10" text-anchor="end"'
        # Drawn only where its own side is clear: toward the next mark, a badge covers it.
        neighbor = any(0 < (x - g["x"] if right else g["x"] - x) < COL * 1.6
                       for x in occupied[(g["lane"], g["category"])])
        badge = f'<text class="count" {place} y="-6">{count}</text>' if len(members) > 1 and not neighbor else ""
        body = f'<title>{esc(tip)}</title><circle class="hit" r="11"/>{marker(g["category"], badge)}'
        where = f'transform="translate({g["x"]:.1f},{g["y"]:.1f})"'
        if first["line"] in in_table:
            aria = f"{g['category']}, line {first['line']}" + (f", {len(members):,} grouped" if len(members) > 1 else "")
            if first["question"]:
                aria += ": " + clip(first["question"], 80)
            out.append(f'<a class="mark" href="#line-{first["line"]}" aria-label="{esc(aria)}" {where}>{body}</a>')
        else:
            out.append(f'<g class="mark" {where}>{body}</g>')
    out.append("</svg>")
    return "".join(out)


def draw_labels(geo):
    height = geo["height"]
    out = [f'<svg class="labels" width="{LABEL_W}" height="{height}" viewBox="0 0 {LABEL_W} {height}" aria-hidden="true">']
    for name, top, subs in geo["geometry"]:
        out.append(f'<line class="rule" x1="0" x2="{LABEL_W}" y1="{top:.1f}" y2="{top:.1f}"/>')
        out.append(f'<text class="lane-name" x="2" y="{top + 14:.1f}"><title>{esc(clip(name, NAME_LIMIT))}</title>{esc(clip(name, 17))}</text>')
        for category, y in subs.items():
            out.append(f'<text class="sub-name" x="{LABEL_W - 8}" y="{y + 3.5:.1f}">{esc(category)}</text>')
    out.append("</svg>")
    return "".join(out)


def legend(events, grouped):
    counts = {c: sum(1 for e in events if e["category"] == c) for c in CATEGORIES}
    items = []
    for c in CATEGORIES:
        if c in KINDS or counts[c]:
            items.append(f'<li><svg width="20" height="20" viewBox="-10 -10 20 20" aria-hidden="true">'
                         f'{marker(c)}</svg>{esc(c)} <span class="muted">({counts[c]:,})</span></li>')
    items.append('<li><svg width="34" height="20" viewBox="0 -10 34 20" aria-hidden="true"><g class="k-neutral">'
                 '<line class="bar" x1="4" x2="30" y1="0" y2="0"/><line class="bar-start" x1="4" x2="4" y1="-5" y2="5"/>'
                 '</g></svg>waiting, from asked to answered</li>')
    if grouped:
        items.append('<li><span class="muted">×N</span> marks that overlapped, grouped</li>')
    return f'<ul class="legend">{"".join(items)}</ul>'


# --- the page --------------------------------------------------------------------------

CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--surface-2:#f3f2ef;--ink:#0b0b0b;--ink-2:#52514e;--ink-3:#6b6a65;
--rule:#e4e3df;--grid:#ecebe7;--link:#1c5cab;--target:#fdf1c7;--k-decide:#2a78d6;--k-approve:#eb6834;
--k-execute:#1baf7a;--k-taste:#eda100;--k-other:#85847e;--on-decide:#fff;--on-approve:#0b0b0b;
--on-execute:#0b0b0b;--on-taste:#0b0b0b}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;
--surface-2:#242422;--ink:#fff;--ink-2:#c3c2b7;--ink-3:#a3a29a;--rule:#3a3a37;--grid:#2c2c2a;--link:#86b6ef;
--target:#3b3522;--k-decide:#3987e5;--k-approve:#d95926;--k-execute:#199e70;--k-taste:#c98500;--k-other:#8f8e87}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--surface-2:#242422;--ink:#fff;--ink-2:#c3c2b7;
--ink-3:#a3a29a;--rule:#3a3a37;--grid:#2c2c2a;--link:#86b6ef;--target:#3b3522;--k-decide:#3987e5;
--k-approve:#d95926;--k-execute:#199e70;--k-taste:#c98500;--k-other:#8f8e87}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 48px;overflow-wrap:break-word}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px}
p{margin:6px 0}a{color:var(--link)}.muted,.meta{color:var(--ink-2)}.meta{font-size:13px;overflow-wrap:anywhere}
.headline{font-size:19px;font-weight:600;margin-top:18px}
.note{font-size:13px;color:var(--ink-2)}
ol.waits{margin:6px 0;padding-left:22px}
.legend{list-style:none;padding:0;margin:16px 0 8px;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px}
.legend li{display:flex;align-items:center;gap:6px}
.chart-row{display:flex;align-items:flex-start;width:fit-content;max-width:100%;border:1px solid var(--rule);
border-radius:6px;background:var(--surface)}
.labels{flex:none;display:block;border-right:1px solid var(--rule)}
.chart-scroll{flex:1 1 auto;min-width:0;overflow-x:auto}
.chart{display:block}
figure{margin:0}figcaption{font-size:13px;color:var(--ink-2);margin-top:6px}
svg text{font:11px system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;fill:var(--ink-2)}
.rule{stroke:var(--rule);stroke-width:1}
.tick line{stroke:var(--grid);stroke-width:1}.tick text,.side-title{text-anchor:middle;fill:var(--ink-3)}
.lane-name{font-weight:600;fill:var(--ink)}.sub-name{text-anchor:end;font-size:10px;fill:var(--ink-3)}
.lane-sum{fill:var(--ink-3)}
.k-DECIDE{--c:var(--k-decide);--on:var(--on-decide)}.k-APPROVE{--c:var(--k-approve);--on:var(--on-approve)}
.k-EXECUTE{--c:var(--k-execute);--on:var(--on-execute)}.k-TASTE{--c:var(--k-taste);--on:var(--on-taste)}
.k-invalidated,.k-other,.k-neutral{--c:var(--k-other);--on:var(--ink-2)}
.shape{fill:var(--c);stroke:var(--surface);stroke-width:3;paint-order:stroke}
.k-invalidated .shape{fill:none;stroke:var(--c);stroke-width:2.5;stroke-linecap:round}
.k-other .shape{fill:var(--surface);stroke:var(--c);stroke-width:1.5}
.glyph{text-anchor:middle;font-size:9px;font-weight:700;fill:var(--on)}
.bar{stroke:var(--c);stroke-width:3;stroke-linecap:round;opacity:.7}.bar-start{stroke:var(--c);stroke-width:1.5;opacity:.8}
.bar-label{text-anchor:middle;font-size:10px;fill:var(--ink-2)}
.count{font-size:9px;fill:var(--ink-2)}
.hit{fill:transparent}
a.mark:focus{outline:none}a.mark:focus-visible .hit,a.mark:hover .hit{stroke:var(--ink);stroke-width:1.5}
.table-wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:13px}
caption{text-align:left;padding:8px 10px;color:var(--ink-2)}
th,td{text-align:left;vertical-align:top;padding:6px 10px;border-top:1px solid var(--rule)}
th{background:var(--surface-2);font-weight:600}
table.events{min-width:760px}td.num{font-variant-numeric:tabular-nums;color:var(--ink-2)}
td .q{font-weight:600}td .item{color:var(--ink-3);font-size:12px;overflow-wrap:anywhere}
td .flag{color:var(--ink-2);font-size:12px}td.wrap{overflow-wrap:anywhere}td.tight{white-space:nowrap}
.g-DECIDE{color:var(--k-decide)}.g-APPROVE{color:var(--k-approve)}.g-EXECUTE{color:var(--k-execute)}
.g-TASTE{color:var(--k-taste)}.g-invalidated,.g-other{color:var(--k-other)}
tr:target{background:var(--target)}
.narrow{display:none}
@media (max-width:1064px){.narrow{display:inline}}
@media (max-width:700px){table.cards{min-width:0}
table.cards thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
table.cards tr{display:block;padding:8px 10px;border-top:1px solid var(--rule)}
table.cards td{display:block;border:0;padding:1px 0}
table.cards td[data-label]::before{content:attr(data-label) ": ";color:var(--ink-3);font-size:12px}}
footer{margin-top:32px;font-size:12px;color:var(--ink-3)}
"""


def kind_cell(e):
    c = e["category"]
    extra = ""
    if c == OTHER:
        raw = "no kind" if e["raw_kind"] is None else e["raw_kind"]
        extra = f' <span class="muted">({esc(raw)})</span>'
    return f'<span class="g-{c}" aria-hidden="true">{TABLE_GLYPH[c]}</span> <span class="kind">{esc(c)}</span>{extra}'


def what_cell(e):
    parts = []
    if e["item"]:
        parts.append(f'<div class="item">{esc(clip(e["item"], NAME_LIMIT))}</div>')
    if e["category"] == INVALIDATED:
        parts.append(f'<div class="q">The standing answer to {esc(clip(e["item"] or "(no item id)", NAME_LIMIT))} was invalidated</div>')
    else:
        parts.append(f'<div class="q">{esc(clip(e["question"])) if e["question"] else "(no question recorded)"}</div>')
        if e["answer"]:
            parts.append(f'<div>→ {esc(clip(e["answer"]))}</div>')
    for note in e["notes"]:
        parts.append(f'<div class="flag">{esc(clip(note, 300))}</div>')
    return "".join(parts)


def evidence_cell(e):
    cell = f"<div>ledger line {e['line']:,}</div>"
    value = e.get("evidence")
    if value is None or value == "":
        return cell
    if is_link(value):
        url = value.strip()
        return cell + f'<div><a href="{esc(url)}" rel="noreferrer">{esc(clip(url, 120))}</a></div>'
    return cell + f"<div>{esc(clip(label(value), 300))}</div>"


def render(name, events, skipped, lines, strict):
    human = [e for e in events if e["category"] in KINDS]
    waits = [e for e in human if e["wait"]]
    backwards = [e for e in human if e["wait_text"] == "answered before it was asked"]
    in_table = {e["line"] for e in events[:TABLE_LIMIT]}
    out = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>Agent timeline · {esc(name)}</title><style>{CSS}</style></head><body><main>",
           "<header><h1>Agent timeline</h1>",
           f'<p class="meta">{esc(name)} · {plural(lines, "line")} read: {plural(len(events), "event")}, '
           f'{len(skipped):,} skipped · {esc(strict)}</p></header>', "<section>"]
    if not events:
        out.append('<p class="headline">' + ("The ledger is empty." if lines == 0 else
                   "No line in the ledger could be read as an event.") + "</p>")
    elif human:
        by_kind = ", ".join(f"{sum(1 for e in human if e['category'] == k):,} {k}" for k in KINDS
                            if any(e["category"] == k for e in human))
        out.append(f'<p class="headline">The human was needed {plural(len(human), "time")}: {by_kind}.</p>')
    elif any(e["category"] == OTHER for e in events):
        # A mistyped kind is not evidence that the human was not needed.
        other = sum(1 for e in events if e["category"] == OTHER)
        out.append(f'<p class="headline">No event had a recognized kind ({other:,} shown as other).</p>'
                   f"<p>An answer counts as the human being needed only when its kind is {', '.join(KINDS[:-1])} or {KINDS[-1]}, "
                   "so this page cannot say whether the human was needed.</p>")
    else:
        out.append('<p class="headline">The human was not needed in any event this ledger recorded.</p>')
    if human:
        sentence = f"Waits recorded for {len(waits):,} of {len(human):,}"
        if waits:
            longest = max(waits, key=lambda e: (e["wait"]["seconds"], -e["line"]))
            who = f", asked by {clip(longest['lane'], NAME_LIMIT)}" if longest["lane"] != DEFAULT_LANE else ""
            sentence += (f": {total([e['wait'] for e in waits])} in total, longest {longest['wait_text']} "
                         f"({longest['category']}, {clip(longest['item'] or 'no item id', NAME_LIMIT)}{who}).")
        else:
            sentence += ". No answer here says when its question was asked; an answer with asked_at gets its wait measured."
        out.append(f"<p>{esc(sentence)}</p>")
        if backwards:
            out.append(f"<p>{esc(plural(len(backwards), 'answer'))} could not be used: answered before it was asked.</p>")
    untimed = sum(1 for e in events if e["when"] is None)
    geo = layout(events) if events else None
    day_only = sum(1 for e in geo["side"] if e["when"] is not None) if geo else 0
    parts = []
    if untimed:
        parts.append(f"{plural(untimed, 'event')} {'has' if untimed == 1 else 'have'} no time recorded")
    if day_only:
        parts.append(f"{plural(day_only, 'event')} {'is' if day_only == 1 else 'are'} recorded to the day only")
    if parts:
        them = "it is" if untimed + day_only == 1 else "they are"
        out.append(f"<p>{esc(' and '.join(parts))}; {them} listed after the axis, in ledger order.</p>")
    if skipped:
        numbers = ", ".join(str(n) for n, _ in skipped[:200])
        more = f" and {len(skipped) - 200:,} more" if len(skipped) > 200 else ""
        reasons = {}
        for _, reason in skipped:
            reasons[reason] = reasons.get(reason, 0) + 1
        why = ", ".join(f"{n:,} {reason}" for reason, n in reasons.items())
        out.append(f"<p>Skipped lines: {numbers}{more} ({esc(why)}).</p>")
    out.append('<p class="note">Answered questions only: a question still waiting has no ledger line yet. '
               "Times with no offset are read as UTC.</p></section>")

    if waits:
        top = sorted(waits, key=lambda e: (-e["wait"]["seconds"], e["line"]))[:5]
        out.append("<section><h2>Longest waits</h2><ol class=\"waits\">")
        for e in top:
            bits = " · ".join(esc(clip(b, 60)) for b in (e["category"], e["item"] or "no item id", e["lane"]))
            link = (f'<a href="#line-{e["line"]}">{esc(e["wait_text"])}</a>' if e["line"] in in_table
                    else esc(e["wait_text"]))
            out.append(f"<li>{link} · {bits} · line {e['line']:,}</li>")
        out.append("</ol></section>")

    if events:
        groups = group_marks(events, geo)
        drawable = [e for e in events if e.get("x_asked") is not None and e["x"] - e["x_asked"] >= 1]
        grouped = any(len(g["events"]) > 1 for g in groups)
        caption = "Time runs left to right"
        if geo["has_axis"]:
            ends = [tick_label(geo["t0"], "full", geo["mode"]), tick_label(geo["t1"], "full", geo["mode"])]
            zone = " UTC" if geo["mode"] == "clock" else ""
            caption += f", {ends[0]} to {ends[1]}{zone}" if ends[0] != ends[1] else f"; every placed event is at {ends[0]}{zone}"
        caption += ". One lane per actor, one row per kind inside it. Each mark links to its row in the table."
        hint = '<span class="narrow"> Scroll the chart sideways to see the whole run.</span>'
        if len(drawable) > MAX_BARS:
            caption += f" Only the {MAX_BARS:,} longest waits are drawn as bars."
        out.append(f"<section><h2>Timeline</h2><figure>{legend(events, grouped)}"
                   f'<div class="chart-row">{draw_labels(geo)}<div class="chart-scroll">'
                   f"{draw_chart(events, geo, groups, drawable, in_table)}</div></div>"
                   f"<figcaption>{esc(caption)}{hint}</figcaption></figure></section>")

        out.append('<section><h2>By actor</h2><div class="table-wrap"><table class="cards"><caption>Every event, '
                   'counted by lane.</caption><thead><tr><th scope="col">Actor</th><th scope="col">Needed the human</th>'
                   '<th scope="col">Waits recorded</th><th scope="col">Total wait</th><th scope="col">Other events</th>'
                   "</tr></thead><tbody>")
        for name in geo["lanes"]:
            mine = [e for e in events if e["shown_lane"] == name]
            h = [e for e in mine if e["category"] in KINDS]
            w = [e["wait"] for e in h if e["wait"]]
            kinds = ", ".join(f"{sum(1 for e in h if e['category'] == k):,} {k}" for k in KINDS
                              if any(e["category"] == k for e in h))
            rest = ", ".join(f"{sum(1 for e in mine if e['category'] == c):,} {c}" for c in (INVALIDATED, OTHER)
                             if any(e["category"] == c for e in mine))
            out.append(f'<tr><td><strong>{esc(clip(name, NAME_LIMIT))}</strong></td>'
                       f'<td data-label="Needed the human">{len(h):,}{": " + kinds if kinds else ""}</td>'
                       f'<td data-label="Waits recorded">{len(w):,} of {len(h):,}</td>'
                       f'<td data-label="Total wait">{esc(total(w)) if w else "not recorded"}</td>'
                       f'<td data-label="Other events">{esc(rest) if rest else "none"}</td></tr>')
        out.append("</tbody></table></div></section>")

        out.append("<section><h2>Every event</h2>")
        if len(events) > TABLE_LIMIT:
            out.append(f"<p>The table shows the first {TABLE_LIMIT:,} of {len(events):,} events, in ledger order; "
                       f"the rest start at ledger line {events[TABLE_LIMIT]['line']:,}.</p>")
        out.append('<div class="table-wrap"><table class="events cards"><caption>In ledger order. The line number is '
                   'the line in the ledger file.</caption><thead><tr><th scope="col">Line</th><th scope="col">Time</th>'
                   '<th scope="col">Actor</th><th scope="col">Kind</th><th scope="col">What happened</th>'
                   '<th scope="col">Wait</th><th scope="col">Evidence</th></tr></thead><tbody>')
        for e in events[:TABLE_LIMIT]:
            out.append(f'<tr id="line-{e["line"]}"><td class="num" data-label="Line">{e["line"]:,}</td>'
                       f'<td data-label="Time">{esc(show_time(e["when"]))}</td>'
                       f'<td data-label="Actor">{esc(clip(e["lane"], NAME_LIMIT))}</td>'
                       f'<td class="tight">{kind_cell(e)}</td><td class="wrap">{what_cell(e)}</td>'
                       f'<td data-label="Wait">{esc(e["wait_text"])}</td><td class="wrap">{evidence_cell(e)}</td></tr>')
        out.append("</tbody></table></div></section>")
    out.append("<footer>Drawn by hsi timeline from the ledger alone: no model and no network. "
               "Per-actor lanes are an idea from microsoft/TinyTroupe (MIT).</footer></main></body></html>\n")
    return "".join(out)


def write_page(path, data):
    """Write the page beside its destination, then move it into place: a failure at any
    point leaves whatever was there before, whole. A symlink is written through, as
    `open(path, "w")` would, and an existing file keeps its permissions."""
    target = os.path.realpath(path)
    folder = os.path.dirname(target)
    os.makedirs(folder, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=folder, prefix="." + os.path.basename(target) + ".", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        try:
            mode = stat.S_IMODE(os.stat(target).st_mode)
        except FileNotFoundError:
            mask = os.umask(0)
            os.umask(mask)
            mode = 0o666 & ~mask
        os.chmod(temp, mode)
        os.replace(temp, target)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def cli(argv):
    parser = argparse.ArgumentParser(prog="hsi timeline",
                                     description="Draw the ledger: where the human was needed, and how long each wait was.")
    parser.add_argument("ledger", help="append-only HSI ledger, one JSON object per line")
    parser.add_argument("-o", "--out", metavar="OUT.html", help="where to write the page; stdout when absent")
    args = parser.parse_args(argv)
    if not os.path.exists(args.ledger):
        print(f"hsi timeline: ledger not found: {args.ledger}", file=sys.stderr)
        return 2
    if args.out and os.path.exists(args.out) and os.path.samefile(args.out, args.ledger):
        print("hsi timeline: -o is the ledger itself; the ledger is append-only, so choose another file",
              file=sys.stderr)
        return 2
    try:
        events, skipped, lines = read_events(args.ledger)
    except OSError as error:
        print(f"hsi timeline: cannot read {args.ledger}: {type(error).__name__}", file=sys.stderr)
        return 2
    page = render(clean(os.path.basename(args.ledger)), events, skipped, lines, strict_verdict(args.ledger))
    data = page.encode("utf-8")  # before anything is opened, so an encoding error cannot cost a file
    try:
        if args.out:
            write_page(args.out, data)
        else:
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
    except OSError as error:
        print(f"hsi timeline: cannot write {args.out or 'stdout'}: {type(error).__name__}", file=sys.stderr)
        return 2
    human = [e for e in events if e["category"] in KINDS]
    print(f"hsi timeline: {plural(lines, 'line')}, {plural(len(events), 'event')}, {len(skipped):,} skipped, "
          f"{plural(len(human), 'human point')}, waits recorded for {sum(1 for e in human if e['wait']):,}"
          f" -> {args.out or 'stdout'}", file=sys.stderr)
    return 0
