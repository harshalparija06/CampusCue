import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "campuscue.db"
DB_PATH.parent.mkdir(exist_ok=True)

st.set_page_config(page_title="CampusCue", page_icon="🎓", layout="wide")

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                due_date TEXT NOT NULL,
                estimated_minutes INTEGER NOT NULL,
                importance INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL UNIQUE,
                packed INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                amount REAL NOT NULL,
                spent_on TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM checklist").fetchone()[0]
        if count == 0:
            con.executemany(
                "INSERT OR IGNORE INTO checklist(item) VALUES (?)",
                [(x,) for x in ["Laptop", "Charger", "Notebook", "Pen", "College ID", "Water bottle"]]
            )

def get_tasks():
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM tasks ORDER BY due_date ASC", con)

def priority_score(row):
    days_left = (date.fromisoformat(row["due_date"]) - date.today()).days
    urgency = 10 if days_left <= 0 else max(1, 10 - days_left)
    return round(urgency * 0.65 + int(row["importance"]) * 2 * 0.35, 1)

init_db()

st.title("🎓 CampusCue")
st.caption("A calmer, more organized college day — powered by Python.")
page = st.sidebar.radio("Navigate", ["Dashboard", "Tasks & Planner", "College Checklist", "Expense Tracker", "Export Data"])

tasks = get_tasks()
pending = tasks[tasks["status"] == "Pending"] if not tasks.empty else tasks
completed_count = int((tasks["status"] == "Completed").sum()) if not tasks.empty else 0

if page == "Dashboard":
    st.subheader("Your overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total tasks", len(tasks))
    c2.metric("Still pending", len(pending))
    c3.metric("Completed", completed_count)
    due_soon = 0
    if not pending.empty:
        due_soon = int(((pd.to_datetime(pending["due_date"]).dt.date - date.today()).apply(lambda x: x.days)).between(0, 3).sum())
    c4.metric("Due in 3 days", due_soon)

    st.divider()
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("#### 🔥 What needs attention")
        if pending.empty:
            st.success("You're all caught up. Add a task when something comes up.")
        else:
            view = pending.copy()
            view["Priority"] = view.apply(priority_score, axis=1)
            view = view.sort_values(["Priority", "due_date"], ascending=[False, True]).head(6)
            for _, task in view.iterrows():
                days = (date.fromisoformat(task["due_date"]) - date.today()).days
                due_label = "Due today" if days == 0 else ("Overdue" if days < 0 else f"Due in {days} day(s)")
                st.write(f"**{task['title']}** · {task['category']} · {due_label} · Priority {task['Priority']}/10")
    with right:
        st.markdown("#### 📊 Completion")
        if len(tasks):
            st.progress(completed_count / len(tasks))
            st.write(f"{completed_count} of {len(tasks)} tasks completed")
            chart = tasks["status"].value_counts()
            st.bar_chart(chart)
        else:
            st.info("Your progress chart will appear after you add tasks.")

elif page == "Tasks & Planner":
    st.subheader("Add a task")
    with st.form("new_task", clear_on_submit=True):
        title = st.text_input("Task name", placeholder="e.g. Complete Python assignment")
        a, b, c = st.columns(3)
        category = a.selectbox("Category", ["Assignment", "Practical", "Exam", "Project", "Personal", "Other"])
        due = b.date_input("Deadline", value=date.today() + timedelta(days=2))
        minutes = c.number_input("Estimated time (minutes)", min_value=5, max_value=1000, value=60, step=5)
        importance = st.slider("Importance", 1, 5, 3, help="1 = low importance, 5 = very important")
        submitted = st.form_submit_button("Add task", type="primary")
        if submitted:
            if not title.strip():
                st.error("Please enter a task name.")
            else:
                with connect() as con:
                    con.execute(
                        "INSERT INTO tasks(title, category, due_date, estimated_minutes, importance, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (title.strip(), category, due.isoformat(), int(minutes), importance, datetime.now().isoformat(timespec="seconds"))
                    )
                st.success("Task added.")
                st.rerun()

    st.divider()
    st.subheader("Your tasks")
    tasks = get_tasks()
    if tasks.empty:
        st.info("No tasks yet. Add your first task above.")
    else:
        show = tasks.copy()
        show["Priority"] = show.apply(priority_score, axis=1)
        st.dataframe(show[["id", "title", "category", "due_date", "estimated_minutes", "importance", "Priority", "status"]],
                     use_container_width=True, hide_index=True)
        task_options = {f"#{r.id} · {r.title} ({r.status})": int(r.id) for r in tasks.itertuples()}
        selected_label = st.selectbox("Choose a task to update", list(task_options))
        selected_id = task_options[selected_label]
        selected_status = tasks.loc[tasks["id"] == selected_id, "status"].iloc[0]
        col1, col2 = st.columns(2)
        new_status = col1.selectbox("Status", ["Pending", "Completed"], index=0 if selected_status == "Pending" else 1)
        if col2.button("Save status"):
            with connect() as con:
                con.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, selected_id))
            st.rerun()
        if st.button("Delete selected task"):
            with connect() as con:
                con.execute("DELETE FROM tasks WHERE id=?", (selected_id,))
            st.rerun()

    st.divider()
    st.subheader("🗓️ Build a simple plan for today")
    available = st.number_input("How many minutes can you study/work today?", min_value=15, max_value=900, value=120, step=15)
    if st.button("Generate my plan"):
        tasks = get_tasks()
        remaining = tasks[tasks["status"] == "Pending"].copy()
        if remaining.empty:
            st.info("No pending tasks to schedule.")
        else:
            remaining["Priority"] = remaining.apply(priority_score, axis=1)
            remaining = remaining.sort_values(["Priority", "due_date"], ascending=[False, True])
            used = 0
            plan = []
            for _, row in remaining.iterrows():
                duration = int(row["estimated_minutes"])
                if used + duration <= available:
                    plan.append((row["title"], duration, row["Priority"]))
                    used += duration
            if plan:
                st.success(f"Suggested focus time: {used} of {available} minutes")
                for i, (name, duration, score) in enumerate(plan, 1):
                    st.write(f"**{i}. {name}** — {duration} min · Priority {score}/10")
                st.caption("This is a suggestion, not a fixed timetable. Break large tasks into smaller tasks if they do not fit.")
            else:
                st.warning("No complete task fits this time window. Try adding more time or splitting a task.")

elif page == "College Checklist":
    st.subheader("🎒 Before you leave")
    with connect() as con:
        rows = con.execute("SELECT id, item, packed FROM checklist ORDER BY item").fetchall()
    for item_id, item, packed in rows:
        checked = st.checkbox(item, value=bool(packed), key=f"check_{item_id}")
        if int(checked) != packed:
            with connect() as con:
                con.execute("UPDATE checklist SET packed=? WHERE id=?", (int(checked), item_id))
            st.rerun()
    st.divider()
    new_item = st.text_input("Add your own checklist item", placeholder="e.g. Lab coat")
    if st.button("Add checklist item"):
        if new_item.strip():
            try:
                with connect() as con:
                    con.execute("INSERT INTO checklist(item) VALUES (?)", (new_item.strip(),))
                st.rerun()
            except sqlite3.IntegrityError:
                st.warning("That item is already on your checklist.")
    if st.button("Reset checklist for tomorrow"):
        with connect() as con:
            con.execute("UPDATE checklist SET packed=0")
        st.rerun()

elif page == "Expense Tracker":
    st.subheader("💸 Track small daily expenses")
    with st.form("expense_form", clear_on_submit=True):
        item = st.text_input("What did you spend on?", placeholder="e.g. Canteen snack")
        x, y, z = st.columns(3)
        amount = x.number_input("Amount (₹)", min_value=1.0, max_value=100000.0, value=30.0, step=5.0)
        spent_on = y.date_input("Date", value=date.today())
        category = z.selectbox("Category", ["Food", "Travel", "Stationery", "College", "Other"])
        add_expense = st.form_submit_button("Save expense", type="primary")
        if add_expense:
            if item.strip():
                with connect() as con:
                    con.execute("INSERT INTO expenses(item, amount, spent_on, category) VALUES (?, ?, ?, ?)",
                                (item.strip(), amount, spent_on.isoformat(), category))
                st.success("Expense saved.")
                st.rerun()
            else:
                st.error("Enter what the expense was for.")
    with connect() as con:
        expenses = pd.read_sql_query("SELECT * FROM expenses ORDER BY spent_on DESC, id DESC", con)
    if not expenses.empty:
        this_month = expenses[pd.to_datetime(expenses["spent_on"]).dt.strftime("%Y-%m") == date.today().strftime("%Y-%m")]
        st.metric("Spent this month", f"₹{this_month['amount'].sum():,.2f}")
        st.dataframe(expenses, use_container_width=True, hide_index=True)
        st.bar_chart(expenses.groupby("category")["amount"].sum())
        if st.button("Clear all expenses"):
            with connect() as con:
                con.execute("DELETE FROM expenses")
            st.rerun()
    else:
        st.info("No expenses recorded yet.")

elif page == "Export Data":
    st.subheader("Export your data")
    with connect() as con:
        task_df = pd.read_sql_query("SELECT * FROM tasks", con)
        expense_df = pd.read_sql_query("SELECT * FROM expenses", con)
        checklist_df = pd.read_sql_query("SELECT * FROM checklist", con)
    for label, frame, filename in [
        ("Tasks", task_df, "campuscue_tasks.csv"),
        ("Expenses", expense_df, "campuscue_expenses.csv"),
        ("Checklist", checklist_df, "campuscue_checklist.csv")
    ]:
        st.markdown(f"**{label}**")
        st.download_button(f"Download {label} CSV", frame.to_csv(index=False).encode("utf-8"), filename, "text/csv")
        st.caption(f"{len(frame)} record(s)")
