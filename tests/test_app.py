from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo

from streamlit.testing.v1 import AppTest

from habits import Store


def by_label(elements, label):
    return next(element for element in elements if element.label == label)


def test_checkin_navigation_restore_and_delete(tmp_path, monkeypatch):
    path = tmp_path / "journal.db"
    monkeypatch.setenv("HABIT_DB_PATH", str(path))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "tracker.py", default_timeout=30).run()
    assert not app.exception
    # Select a past year so this test works regardless of today's month length.
    by_label(app.number_input, "Year").set_value(2024).run()
    by_label(app.selectbox, "Month").set_value(2).run()
    by_label(app.selectbox, "Check-in day").set_value(29).run()
    by_label(app.checkbox, "Gym 💪").check()
    by_label(app.checkbox, "Games").check()
    by_label(app.number_input, "Sleep last night (hours)").set_value(7.5)
    by_label(app.text_area, "Daily reflection").set_value("Good session")
    by_label(app.button, "Save daily check-in").click().run()
    assert not app.exception
    entry = Store(path).all()["2024-02-29"]
    assert entry == {"good": ["gym"], "bad": ["games"], "sleep": 7.5, "notes": "Good session"}
    # An unlogged day must not inherit the prior day's values.
    by_label(app.selectbox, "Check-in day").set_value(28).run()
    assert not by_label(app.checkbox, "Gym 💪").value
    assert by_label(app.number_input, "Sleep last night (hours)").value is None
    by_label(app.selectbox, "Check-in day").set_value(29).run()
    assert by_label(app.checkbox, "Gym 💪").value
    assert by_label(app.checkbox, "Games").value
    # Restore invalidates date widgets so restored values appear, not stale edits.
    Store(path).save(date(2024, 2, 29), dict(entry, good=[]))
    app.session_state["revision"] = 1
    app.run()
    assert not by_label(app.checkbox, "Gym 💪").value
    by_label(app.checkbox, "I understand this will return the day to not logged").check().run()
    by_label(app.button, "Delete saved day").click().run()
    assert not app.exception
    assert Store(path).all() == {}
    assert not by_label(app.checkbox, "Games").value


def test_future_dates_are_read_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HABIT_DB_PATH", str(tmp_path / "journal.db"))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "tracker.py", default_timeout=30).run()
    by_label(app.number_input, "Year").set_value(datetime.now(ZoneInfo("Asia/Karachi")).year + 1).run()
    assert by_label(app.button, "Save daily check-in").disabled
    assert by_label(app.checkbox, "Gym 💪").disabled
    assert not app.exception
