"""LOCKIN — a personal, spreadsheet-inspired daily habit journal."""

import calendar
import sqlite3
from datetime import date, datetime
from io import StringIO
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from habits import BAD_HABITS, GOOD_HABITS, GOAL, Store, daily_stats, empty_entry, month_dates, period_stats

st.set_page_config(page_title="LOCKIN · Habit Tracker", page_icon="🎯", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1500px; padding-top: 2.5rem;}
[data-testid="stSidebar"] {border-right: 1px solid #35415c;}
h1 {letter-spacing: -.045em; font-size: 2.8rem !important;}
h2 {letter-spacing: -.025em;}
[data-testid="stMetric"] {background: #253150; padding: 18px; border-radius: 12px; border: 1px solid #35415c;}
[data-testid="stMetricLabel"] {color: #b9c5db;}
[data-testid="stMetricValue"] {color: #a5ebd8;}
[data-testid="stForm"] {background: #1b2640; border-color: #35415c;}
.eyebrow {color: #a5ebd8; font-size: .8rem; letter-spacing: .2em; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

try:
    store = Store()
    entries = store.all()
except (OSError, sqlite3.Error):
    st.error("The journal could not be opened. Check HABIT_DB_PATH and the server's write permissions.")
    st.stop()

today = datetime.now(ZoneInfo("Asia/Karachi")).date()
WEEK_COLORS = ["#eba0a6", "#a58ce5", "#a8c9e7", "#efed81", "#9bc98d"]

with st.sidebar:
    st.markdown("### 🎯 LOCKIN")
    st.caption("Small actions. Stronger days.")
    st.divider()
    st.markdown("##### CALENDAR SETTINGS")
    year = int(st.number_input("Year", min_value=1900, max_value=2100, value=today.year))
    month = st.selectbox("Month", range(1, 13), index=today.month - 1,
                         format_func=lambda value: calendar.month_name[value])
    days = month_dates(year, month)
    day_number = st.selectbox("Check-in day", range(1, len(days) + 1),
                              index=min(today.day, len(days)) - 1,
                              format_func=lambda value: f"{value:02d} · {date(year, month, value):%A}")
    selected = date(year, month, day_number)
    st.caption("Dates use Asia/Karachi time.")
    st.divider()
    st.markdown("**YOUR DAILY RULES**")
    st.caption("✓ Good habit = completed\n\n✓ Bad habit = happened\n\nSave once you’ve reviewed the whole day.")
    st.info("Personal journal: everyone with access to this deployment shares the same data. Keep access private.")
    st.caption("Saved on this server. Streamlit Cloud storage may reset on restart or redeploy—download backups regularly.")

st.markdown('<div class="eyebrow">YOUR PERSONAL DISCIPLINE DASHBOARD</div>', unsafe_allow_html=True)
st.title("LOCKIN Habit Tracker")
st.caption(f"{calendar.month_name[month]} {year} · Build the good. Break the bad. Show up every day.")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

summary = period_stats(days, entries)
a, b, c, d = st.columns(4)
a.metric("MONTHLY CONSISTENCY", f"{summary['percent']}%" if summary["percent"] is not None else "—",
         help="Average score across saved check-ins only; unlogged days earn no points.")
b.metric("DAYS CHECKED IN", f"{summary['logged']} / {len(days)}")
c.metric("POINTS EARNED", f"{summary['score']} / {summary['possible']}", help="Denominator: 10 points per saved day.")
d.metric("AVERAGE SLEEP", f"{summary['sleep']:g} h" if summary["sleep"] is not None else "—")
st.write("")

checkin_tab, month_tab, backup_tab = st.tabs(["☑ Daily check-in", "▦ Monthly overview", "↗ Backup & data"])

with checkin_tab:
    st.subheader(f"{selected:%A, %d %B %Y}")
    existing = entries.get(selected.isoformat())
    entry = existing or empty_entry()
    if selected > today:
        st.info("This date is in the future. Check-ins open on that day.")
    elif existing is None:
        st.caption("NOT LOGGED · Tick what you completed and what happened, then save the day.")
    else:
        stats = daily_stats(existing)
        st.caption(f"SAVED · {stats['score']}/{GOAL} points · {stats['percent']}% · You can update this day anytime.")
    # Date-specific widget identities prevent one day's values leaking into another.
    suffix = f"{selected.isoformat()}-{st.session_state.get('revision', 0)}"
    with st.form(f"checkin-{suffix}"):
        good_col, bad_col = st.columns(2)
        with good_col:
            st.markdown("### 🌱 Good habits")
            st.caption("Tick each habit you completed.")
            good = [key for key, label in GOOD_HABITS if st.checkbox(
                label, value=key in entry["good"], key=f"{suffix}-good-{key}", disabled=selected > today)]
        with bad_col:
            st.markdown("### 🧯 Bad habits")
            st.caption("Tick only if it happened. Unticked = avoided after saving.")
            bad = [key for key, label in BAD_HABITS if st.checkbox(
                label, value=key in entry["bad"], key=f"{suffix}-bad-{key}", disabled=selected > today)]
        st.divider()
        sleep = st.number_input("Sleep last night (hours)", min_value=0.0, max_value=24.0,
                                step=0.5, value=float(entry["sleep"]) if entry["sleep"] is not None else None,
                                placeholder="Optional · e.g. 7.5", key=f"{suffix}-sleep", disabled=selected > today)
        notes = st.text_area("Daily reflection", value=entry["notes"], max_chars=4000,
                             placeholder="What went well? What will you do differently tomorrow?",
                             key=f"{suffix}-notes", disabled=selected > today)
        st.caption("Score = good habits completed + bad habits avoided (10 possible points). Sleep and notes don’t affect your score.")
        submitted = st.form_submit_button("Save daily check-in", type="primary", disabled=selected > today)
    if submitted:
        try:
            store.save(selected, {"good": good, "bad": bad, "sleep": sleep, "notes": notes})
        except (OSError, sqlite3.Error):
            st.error("Could not save your check-in. Your changes are still in the form; check the server's storage and retry.")
        else:
            st.session_state.flash = f"Check-in saved for {selected:%d %B %Y}."
            st.rerun()
    if existing is not None:
        with st.expander("Remove this check-in"):
            confirm = st.checkbox("I understand this will return the day to not logged", key=f"delete-confirm-{suffix}")
            if st.button("Delete saved day", disabled=not confirm, key=f"delete-{suffix}"):
                store.delete(selected)
                st.session_state.revision = st.session_state.get("revision", 0) + 1
                st.session_state.flash = "Check-in removed. The day is now not logged."
                st.rerun()

with month_tab:
    st.subheader("The month at a glance")
    st.caption("Use the sidebar to choose a day, then edit it in Daily check-in. Scroll tables horizontally on smaller screens.")
    fig = go.Figure(go.Scatter(
        x=days, y=[daily_stats(entries.get(day.isoformat()))["percent"] for day in days],
        mode="lines+markers", line={"color": "#a5ebd8", "width": 3},
        marker={"size": 6}, fill="tozeroy", fillcolor="rgba(165,235,216,.10)", connectgaps=False,
        hovertemplate="%{x|%d %b}: %{y}%<extra></extra>"))
    fig.update_layout(height=240, margin=dict(l=0, r=0, t=15, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#253150",
                      yaxis=dict(range=[0, 105], ticksuffix="%", gridcolor="#3b4763"),
                      xaxis=dict(tickformat="%d %b", dtick=604800000), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    def habit_grid(habits, field):
        rows = []
        for key, label in habits:
            row = {"Habit": label}
            for day in days:
                saved = entries.get(day.isoformat())
                row[f"{day.day:02d} {day:%a}"] = "—" if saved is None else ("✓" if key in saved[field] else "·")
            rows.append(row)
        frame = pd.DataFrame(rows).set_index("Habit")

        def colors(column):
            week = (int(column.name.split()[0]) - 1) // 7
            return [f"color: {WEEK_COLORS[week]}; background-color: #253150; text-align: center" for _ in column]

        st.dataframe(frame.style.apply(colors), use_container_width=True, height=(len(rows) + 1) * 35 + 3)

    st.markdown("### 🌱 Good habits")
    st.caption("✓ Completed · · Not completed · — Not logged")
    habit_grid(GOOD_HABITS, "good")
    st.markdown("### 🧯 Bad habits")
    st.caption("✓ Happened · · Avoided · — Not logged. A check here is a lapse, not a positive achievement.")
    habit_grid(BAD_HABITS, "bad")

    st.markdown("### 📊 Progress")
    progress = {label: [] for label in ("Score", "Goal", "Left", "Bad habits")}
    for day in days:
        saved = entries.get(day.isoformat())
        values = daily_stats(saved)
        for label, value in (("Score", values["score"]), ("Goal", GOAL if saved else None),
                             ("Left", values["left"]), ("Bad habits", values["bad"])):
            progress[label].append("—" if value is None else str(value))
    st.dataframe(pd.DataFrame(progress, index=[f"{day.day:02d}" for day in days]).T, use_container_width=True)

    st.markdown("#### Weekly progress")
    st.caption("Like the sheet: Week 1 = days 1–7, Week 2 = 8–14, and so on. Percentages use saved days only.")
    columns = st.columns((len(days) + 6) // 7)
    for index, column in enumerate(columns):
        week_days = days[index * 7:(index + 1) * 7]
        week = period_stats(week_days, entries)
        with column:
            st.markdown(f"**Week {index + 1} · {week_days[0].day}–{week_days[-1].day}**")
            st.metric("Completion", f"{week['percent']}%" if week["percent"] is not None else "—")
            st.progress((week["percent"] or 0) / 100)
            st.caption(f"{week['score']}/{week['possible']} points · {week['logged']}/{len(week_days)} days logged")

    st.markdown("### 🌙 Sleep tracker")
    sleep_values = [entries.get(day.isoformat(), {}).get("sleep") for day in days]
    sleep_fig = go.Figure(go.Scatter(x=days, y=sleep_values, mode="lines+markers",
                                    line=dict(color="#b4c9ed"), fill="tozeroy", connectgaps=False,
                                    fillcolor="rgba(180,201,237,.15)",
                                    hovertemplate="%{x|%d %b}: %{y} hours<extra></extra>"))
    sleep_fig.add_hline(y=8, line_dash="dot", line_color="#9de5d2", annotation_text="8h reference")
    sleep_fig.update_layout(height=260, margin=dict(l=0, r=0, t=20, b=0),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#253150",
                            yaxis=dict(title="Hours", rangemode="tozero"), xaxis=dict(tickformat="%d %b"))
    st.plotly_chart(sleep_fig, use_container_width=True)
    st.caption("Blank sleep entries stay blank; 0 hours is recorded as zero, not missing.")
    st.dataframe(pd.DataFrame({f"{day.day:02d}": ["—" if value is None else f"{value:g} h"]
                              for day, value in zip(days, sleep_values)}, index=["Sleep"]), use_container_width=True)

with backup_tab:
    st.subheader("Keep your progress safe")
    st.warning("SQLite saves across reruns on this server, but Streamlit Community Cloud does not guarantee persistent local files. Export a JSON backup before redeploying and regularly while using the app.")
    st.download_button("Download full backup (.json)", store.export(),
                       file_name=f"lockin-backup-{today}.json", mime="application/json")
    csv_rows = []
    for day in days:
        saved = entries.get(day.isoformat())
        values = daily_stats(saved)
        row = {"Date": day.isoformat(), "Logged": saved is not None,
               "Score": values["score"], "Goal": GOAL if saved else None,
               "Percent": values["percent"], "Left": values["left"],
               "Bad habits": values["bad"], "Sleep hours": saved["sleep"] if saved else None,
               "Notes": saved["notes"] if saved else ""}
        for field, habits in (("good", GOOD_HABITS), ("bad", BAD_HABITS)):
            for key, label in habits:
                row[f"{field.title()}: {label}"] = (key in saved[field]) if saved else None
        csv_rows.append(row)
    # Neutralize spreadsheet formula prefixes in user-entered notes.
    for row in csv_rows:
        if row["Notes"].lstrip().startswith(("=", "+", "-", "@")):
            row["Notes"] = "'" + row["Notes"]
    buffer = StringIO()
    pd.DataFrame(csv_rows).to_csv(buffer, index=False)
    st.download_button("Download selected month (.csv)", buffer.getvalue(),
                       file_name=f"lockin-{year}-{month:02d}.csv", mime="text/csv")
    st.divider()
    st.markdown("#### Restore a backup")
    st.caption("Merges all dates from a LOCKIN JSON backup. Matching dates are overwritten; other dates are kept.")
    upload = st.file_uploader("JSON backup", type=["json"])
    approve = st.checkbox("I understand matching dates will be overwritten")
    if st.button("Restore backup", disabled=upload is None or not approve):
        if upload.size > 5 * 1024 * 1024:
            st.error("Backup must be smaller than 5 MB.")
        else:
            try:
                count = store.restore(upload.getvalue())
            except ValueError as exc:
                st.error(str(exc))
            except (OSError, sqlite3.Error):
                st.error("Could not restore the backup. Check the server's storage and retry.")
            else:
                st.session_state.revision = st.session_state.get("revision", 0) + 1
                st.session_state.flash = f"Restored {count} check-ins."
                st.rerun()
