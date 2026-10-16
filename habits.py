"""Date-aware habit tracking and local persistence, independent of Streamlit."""

import calendar
import json
import os
import sqlite3
from datetime import date
from pathlib import Path

GOOD_HABITS = (
    ("wake_5", "Wake up at 5AM ⏰"),
    ("gym", "Gym 💪"),
    ("protein", "Protein shake 🥕"),
    ("prayer", "Namaz & Quran"),
    ("productive", "Be productive"),
    ("indeed", "Lock in on Indeed"),
)
BAD_HABITS = (
    ("porn", "Porn"),
    ("games", "Games"),
    ("smoking", "Smoking"),
    ("gambling", "Gambling"),
)
GOOD_IDS = {key for key, _ in GOOD_HABITS}
BAD_IDS = {key for key, _ in BAD_HABITS}
GOAL = len(GOOD_HABITS) + len(BAD_HABITS)


def month_dates(year, month):
    return [date(year, month, day) for day in range(1, calendar.monthrange(year, month)[1] + 1)]


def empty_entry():
    return {"good": [], "bad": [], "sleep": None, "notes": ""}


def validate_entry(entry):
    if not isinstance(entry, dict) or set(entry) != {"good", "bad", "sleep", "notes"}:
        raise ValueError("Each check-in must contain good, bad, sleep and notes.")
    for field, allowed in (("good", GOOD_IDS), ("bad", BAD_IDS)):
        values = entry[field]
        if (not isinstance(values, list) or any(not isinstance(v, str) for v in values)
                or len(values) != len(set(values)) or not set(values) <= allowed):
            raise ValueError(f"Invalid {field} habit selections.")
    sleep = entry["sleep"]
    if sleep is not None and (type(sleep) not in (int, float) or not 0 <= sleep <= 24):
        raise ValueError("Sleep must be between 0 and 24 hours, or null.")
    if not isinstance(entry["notes"], str) or len(entry["notes"]) > 4000:
        raise ValueError("Notes must be text up to 4,000 characters.")
    return entry


def daily_stats(entry):
    """Only a saved check-in earns credit for avoided bad habits."""
    if entry is None:
        return {"score": None, "percent": None, "left": None, "bad": None}
    score = len(entry["good"]) + len(BAD_HABITS) - len(entry["bad"])
    return {"score": score, "percent": round(score / GOAL * 100),
            "left": GOAL - score, "bad": len(entry["bad"])}


def period_stats(days, entries):
    logged = [entries[d.isoformat()] for d in days if d.isoformat() in entries]
    earned = sum(daily_stats(entry)["score"] for entry in logged)
    possible = len(logged) * GOAL
    sleeps = [entry["sleep"] for entry in logged if entry["sleep"] is not None]
    return {"logged": len(logged), "score": earned, "possible": possible,
            "percent": round(earned / possible * 100) if possible else None,
            "sleep": round(sum(sleeps) / len(sleeps), 1) if sleeps else None}


class Store:
    """A single-user SQLite journal. Each operation opens a short-lived connection."""

    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("HABIT_DB_PATH", "data/habits.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS entries (day TEXT PRIMARY KEY, payload TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=20)

    def all(self):
        with self.connect() as connection:
            return {day: json.loads(payload) for day, payload in connection.execute(
                "SELECT day, payload FROM entries ORDER BY day")}

    def save(self, day, entry):
        validate_entry(entry)
        with self.connect() as connection:
            connection.execute("INSERT INTO entries(day, payload) VALUES (?, ?) "
                               "ON CONFLICT(day) DO UPDATE SET payload=excluded.payload",
                               (day.isoformat(), json.dumps(entry, allow_nan=False)))

    def delete(self, day):
        with self.connect() as connection:
            connection.execute("DELETE FROM entries WHERE day = ?", (day.isoformat(),))

    def export(self):
        return json.dumps({"version": 1, "entries": self.all()}, indent=2, ensure_ascii=False)

    def restore(self, raw):
        """Validate the entire backup before atomically merging it into the journal."""
        try:
            backup = json.loads(raw)
        except (ValueError, TypeError, UnicodeError) as exc:
            raise ValueError("Upload a valid JSON backup.") from exc
        if (not isinstance(backup, dict) or type(backup.get("version")) is not int
                or backup["version"] != 1 or not isinstance(backup.get("entries"), dict)):
            raise ValueError("This is not a supported LOCKIN backup (version 1).")
        rows = []
        for day, entry in backup["entries"].items():
            try:
                parsed = date.fromisoformat(day)
            except (ValueError, TypeError) as exc:
                raise ValueError("Backup contains an invalid date.") from exc
            if parsed.isoformat() != day:
                raise ValueError("Backup dates must use YYYY-MM-DD.")
            validate_entry(entry)
            rows.append((day, json.dumps(entry, allow_nan=False)))
        with self.connect() as connection:
            connection.executemany("INSERT INTO entries(day, payload) VALUES (?, ?) "
                                   "ON CONFLICT(day) DO UPDATE SET payload=excluded.payload", rows)
        return len(rows)
