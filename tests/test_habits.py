import json
from datetime import date

import pytest

from habits import BAD_IDS, GOOD_IDS, Store, daily_stats, empty_entry, month_dates, period_stats


def test_calendar_boundaries():
    assert len(month_dates(2024, 2)) == 29
    assert len(month_dates(2025, 2)) == 28
    assert len(month_dates(2026, 4)) == 30
    assert month_dates(2026, 12)[-1] == date(2026, 12, 31)


def test_unlogged_days_do_not_earn_credit():
    assert daily_stats(None)["score"] is None
    assert daily_stats(empty_entry())["score"] == 4
    assert daily_stats({"good": list(GOOD_IDS), "bad": [], "sleep": None, "notes": ""})["score"] == 10
    assert daily_stats({"good": [], "bad": list(BAD_IDS), "sleep": None, "notes": ""})["score"] == 0


def test_aggregates_only_saved_days_and_sleep_zero():
    days = month_dates(2026, 10)
    first = dict(empty_entry(), sleep=0)
    second = dict(empty_entry(), good=list(GOOD_IDS), sleep=8)
    entries = {days[0].isoformat(): first, days[1].isoformat(): second}
    stats = period_stats(days, entries)
    assert stats == {"logged": 2, "score": 14, "possible": 20, "percent": 70, "sleep": 4.0}
    assert period_stats(days, {})["percent"] is None
    assert period_stats(days, {})["sleep"] is None


def test_persistence_updates_delete_and_date_isolation(tmp_path):
    path = tmp_path / "data" / "test.sqlite3"
    store = Store(path)
    first, second = date(2026, 1, 1), date(2025, 1, 1)
    store.save(first, empty_entry())
    store.save(second, dict(empty_entry(), notes="Another year"))
    store.save(first, dict(empty_entry(), good=["gym"], sleep=7.5))
    reopened = Store(path)
    assert reopened.all()[first.isoformat()]["good"] == ["gym"]
    assert reopened.all()[second.isoformat()]["notes"] == "Another year"
    reopened.delete(first)
    assert list(reopened.all()) == [second.isoformat()]


def test_backup_round_trip_merge_and_atomic_validation(tmp_path):
    source, target = Store(tmp_path / "source.db"), Store(tmp_path / "target.db")
    source.save(date(2026, 10, 1), dict(empty_entry(), notes="🌱", sleep=0))
    target.save(date(2026, 9, 1), empty_entry())
    assert target.restore(source.export()) == 1
    assert len(target.all()) == 2
    original = target.all()
    malformed = json.loads(source.export())
    malformed["entries"]["2026-10-02"] = dict(empty_entry(), sleep=25)
    with pytest.raises(ValueError):
        target.restore(json.dumps(malformed))
    assert target.all() == original
    malformed = json.loads(source.export())
    malformed["entries"]["2026-10-01"]["notes"] = "replacement"
    target.restore(json.dumps(malformed))
    assert target.all()["2026-10-01"]["notes"] == "replacement"


@pytest.mark.parametrize("raw", ["not-json", "[]", '{"version":2,"entries":{}}',
    '{"version":1,"entries":{"2026-02-30":{}}}',
    '{"version":1,"entries":{"20261001":{}}}'])
def test_reject_invalid_backup(tmp_path, raw):
    with pytest.raises(ValueError):
        Store(tmp_path / "test.db").restore(raw)


@pytest.mark.parametrize("change", [{"good": ["unknown"]}, {"bad": ["games", "games"]},
    {"sleep": float("nan")}, {"sleep": True}, {"sleep": -1}, {"notes": 12}, {"good": [True]}])
def test_reject_invalid_entries(tmp_path, change):
    with pytest.raises(ValueError):
        Store(tmp_path / "test.db").save(date(2026, 10, 1), dict(empty_entry(), **change))
