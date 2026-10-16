# LOCKIN Habit Tracker

A personal Streamlit journal inspired by the supplied **LOCKIN HABIT TRACKER** PDF: navy spreadsheet-style monthly grids, separate good/bad habits, weekly progress, and sleep tracking.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run tracker.py
```

The main entrypoint remains `tracker.py`, so existing Streamlit deployments do not need an entrypoint change. Python 3.11+ is recommended. No remote images, Google credentials, or spreadsheet API are needed.

## Daily workflow

1. Select the year, month and check-in day in the sidebar (Asia/Karachi time).
2. Under **Daily check-in**, tick completed good habits and bad habits that **happened**. These lists follow the reference PDF: wake at 5AM, gym, protein shake, Namaz & Quran, productivity and Indeed; porn, games, smoking and gambling.
3. Optionally enter last night's sleep hours and a reflection, then **Save daily check-in**. Unsaved edits are not persisted; save before changing dates. Reopen any past day to edit it. Future dates are read-only.
4. **Monthly overview** shows separate good/bad grids, the daily score trend, progress rows, five (or four) weekly summaries, and sleep. Tables scroll horizontally on narrow screens. Edit a date through the sidebar and Daily check-in, rather than directly in the overview tables.
5. Download backups regularly from **Backup & data**. Restore merges a JSON backup and overwrites matching dates only, after confirmation. CSV exports the selected month for spreadsheet use.

### Scoring and missing data

- Good habit completed: **+1**.
- Bad habit avoided: **+1**; checking a bad habit means it happened and earns **0** for that habit.
- Daily goal: **10** (six good habits + four bad habits).
- `Left = 10 − score`; `Bad habits` counts the bad habits that happened.
- An unlogged day is **not** a day with all bad habits avoided: it has no score. Saving confirms that you reviewed the whole day, so saving an entirely unticked day scores 4/10.
- Monthly/weekly percentages use **saved days only**. Check-in coverage is shown separately. This deliberately differs from the PDF's example, which shows 40% on entirely unchecked dates.
- Week 1 is days 1–7, Week 2 is 8–14, Week 3 is 15–21, Week 4 is 22–28, and Week 5 contains the remaining days, matching the reference rather than calendar weeks.
- Sleep is optional and independent of the score. Missing hours are excluded from averages; zero hours are a valid recorded value. The chart's 8-hour line is a reference, not a scored goal.
- PDF example checkmarks/sleep values are **not** imported as real personal history.

## Persistence, privacy and Streamlit deployment

Check-ins are stored in SQLite at `data/habits.sqlite3`, not in Streamlit session state. They survive page reloads and server restarts **when the underlying filesystem is retained**. All database files, local data and Streamlit secrets are gitignored.

**This is a single-user app with a shared journal, not an authenticated multi-user service.** Anyone who can access a deployment can read, change, export or delete its data. Restrict access to your deployment (for example, private Streamlit sharing). Do not publicly deploy sensitive personal history without access controls.

**Streamlit Community Cloud local storage is not guaranteed durable.** A restart/reboot/redeploy can lose the database. The local SQLite database alone is not a cloud durability solution. Download full JSON backups regularly and restore them after a reset. Backups contain sensitive history and notes; keep them private. CSV is for analysis, not restore.

For a self-hosted deployment with a persistent disk, set an environment variable before launching:

```bash
export HABIT_DB_PATH=/path/to/persistent-volume/habits.sqlite3
streamlit run tracker.py
```

The path must be writable by the server. Guaranteed automatic cloud durability would require a separately provisioned database or persistent volume; neither is bundled or configured by this PR. Do not store database files in Git.

The Streamlit config binds to `0.0.0.0` for hosted previews and leaves built-in CORS/XSRF protections enabled.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover leap years/month lengths, score direction, unlogged days, sleep averages, SQLite reopening/updating/date isolation/deleting, backup round-trips/merges/atomic rejection, and Streamlit check-in/save/navigation/deletion/restore refresh/future-date behavior. No real journal data is needed.
