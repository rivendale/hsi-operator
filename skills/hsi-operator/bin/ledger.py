"""Read and validate the append-only HSI ledger for the CLI and its adapter."""

import datetime
import json
import re


KINDS = ("DECIDE", "APPROVE", "EXECUTE", "TASTE")
BASES = ("Data", "Estimate", "Assumption", "Opinion")


class LedgerError(ValueError):
    pass


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def invalid_answer_field(row):
    """Name the first missing or invalid answer field."""
    if not isinstance(row, dict):
        return "answer"
    if "invalidated" in row:
        return "invalidated"
    for field in ("item_id", "question", "answer", "words", "reasoning", "invalidated_by"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            return field
    if "setpoint_id" not in row or (row["setpoint_id"] is not None and
                                     not isinstance(row["setpoint_id"], str)):
        return "setpoint_id"
    if row.get("kind") not in KINDS:
        return "kind"
    if row.get("basis") not in BASES:
        return "basis"
    if not valid_date(row.get("date")):
        return "date"
    if "supersedes_reason" in row and (not isinstance(row["supersedes_reason"], str) or
                                        not row["supersedes_reason"].strip()):
        return "supersedes_reason"
    return None


def read_ledger(path):
    """Return each item's latest answer, its line, and any later invalidation."""
    standing = {}
    try:
        with open(path, encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict) or not isinstance(row.get("item_id"), str) or not row["item_id"].strip():
                        raise ValueError("expected an object with item_id")
                    item_id = row["item_id"]
                    if set(row) == {"item_id", "invalidated"}:
                        event = row["invalidated"]
                        if (not isinstance(event, dict) or
                                not valid_date(event.get("date")) or
                                not isinstance(event.get("evidence"), str) or
                                not event["evidence"].strip() or
                                item_id not in standing or standing[item_id]["invalidated"]):
                            raise ValueError("invalid invalidation")
                        standing[item_id]["invalidated"] = event
                        standing[item_id]["invalidation_line"] = number
                    else:
                        invalid = invalid_answer_field(row)
                        if invalid:
                            raise ValueError(f"invalid answer {invalid}")
                        standing[item_id] = {"answer": row, "answer_line": number,
                                             "invalidated": None, "invalidation_line": None}
                except (ValueError, TypeError) as error:
                    raise LedgerError(f"ledger line {number}: {error}") from error
    except FileNotFoundError:
        return {}
    return standing
