# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

A lightweight offline TODO list desktop application built with Python + tkinter + SQLite, running on Windows. All UI text is in Chinese.

## Tech Stack

- **Language**: Python 3.9+
- **GUI**: tkinter (Python built-in, zero external dependency)
- **Database**: SQLite3 via Python's built-in `sqlite3` module
- **Platform**: Windows (primary target)

## Commands

- All shell commands MUST use PowerShell, not bash. The PowerShell path is `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`.
- Git path: `C:\Program Files\Git\bin\git.exe`.
- Commit after each completed feature with a clear commit message summarizing what was done.

```powershell
# Run the application (single entry point, no build step)
python main.py
```

No external dependencies for development. tkinter, sqlite3, and json are all Python standard library modules.

## Packaging

```powershell
# Install PyInstaller (one-time)
pip install pyinstaller

# Package as single .exe file
pyinstaller --onefile --windowed --name TODOList main.py
# Output: dist/TODOList.exe
```

The .exe bundles Python and all dependencies, so end users don't need Python installed.

## Project Architecture

```
TODOLIST/
├── main.py              # Entry point, tkinter main window + event loop
├── models.py            # Task data model + SQLite CRUD operations
├── views.py             # Tkinter UI components (task list, dialogs, timer)
├── controllers.py       # Event handlers, wiring between views and models
├── utils.py             # Cache cleaning, export/import helpers
├── data/
│   └── todolist.db      # SQLite database (auto-created on first run)
└── README.md
```

Architecture follows a simple MVC pattern:
- **models.py** — Defines the Task data class, database connection, and all SQL operations (create table, add task, update task, delete task, query tasks, clear cache).
- **views.py** — All tkinter widgets: main window layout, task list treeview, add/edit task dialogs, timer display, menu bar.
- **controllers.py** — Bridges UI events to model operations. Handles button clicks, menu actions, timer start/stop logic.
- **utils.py** — Cache/temp file cleanup logic, data integrity checks.

Key data objects:
- `Task`: id, title, description, created_at, deadline, status (pending/in_progress/done), timer_duration_seconds, timer_started_at

Storage decisions:
- SQLite database in `data/` directory, auto-created with schema if not present
- Timer state managed in-memory, synced to DB on task update

Cache cleaning:
- Remove completed tasks older than a configurable threshold
- Vacuum SQLite database to reclaim space
- Optionally reset timer history

## UI Language

All interface text (labels, buttons, menus, dialogs, status bar, messages) must be in Chinese.

## README

After all features are complete, write README.md with:
- App description and features overview
- Screenshot or UI description
- How to run from source (`python main.py`)
- How to use the packaged .exe
- Basic usage guide (add tasks, start timer, clean cache, etc.)
