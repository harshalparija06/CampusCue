# CampusCue 🎓

A lightweight student-life organizer built with Python, Streamlit, and SQLite.

## The everyday problem
Students often manage assignments, practicals, deadlines, things to carry, and small expenses in separate places. CampusCue brings these everyday tasks into one simple dashboard.

## Features
- Task manager for assignments, practicals, exams, projects, and personal tasks
- Priority score based on deadline urgency and importance
- Daily plan generator that fits complete tasks into available time
- Reusable college packing checklist
- Daily expense tracker with category chart
- CSV exports for tasks, expenses, and checklist
- Local SQLite database: your data stays on your machine

## Tech stack
- Python
- Streamlit
- SQLite
- Pandas

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR-USERNAME/CampusCue.git
cd CampusCue
```

### 2. Create and activate a virtual environment (recommended)
```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

Your browser should open the CampusCue dashboard.

## Project structure
```text
CampusCue/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    └── .gitkeep
```

The SQLite database is created automatically at `data/campuscue.db` the first time the app runs.

## Priority logic
The app calculates a simple score using:
- Deadline urgency (65%)
- User-selected importance (35%)

This is a transparent heuristic, not an AI prediction. You can experiment with the weights and explain the design in your project presentation.

## Future improvements
- Add recurring tasks and timetable support
- Add optional email or desktop reminders
- Add weekly spending limits
- Add user accounts and cloud sync
- Add tests for the priority calculation and database operations

## Privacy
This starter version stores data locally in SQLite. Do not commit your personal database to GitHub.
