import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "todolist.db")


def _get_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT    NOT NULL,
            description     TEXT    DEFAULT '',
            status  TEXT    DEFAULT 'pending',
            created_at      TEXT    NOT NULL,
            deadline TEXT,
            estimated_minutes INTEGER DEFAULT 0,
            elapsed_seconds  INTEGER DEFAULT 0,
            timer_started_at TEXT,
            reminder_minutes INTEGER DEFAULT 0,
            reminder_fired  INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    _migrate(conn)
    conn.close()


def _migrate(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
    if "reminder_minutes" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN reminder_minutes INTEGER DEFAULT 0")
    if "reminder_fired" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN reminder_fired INTEGER DEFAULT 0")


def add_task(title, description="", deadline=None, estimated_minutes=0, reminder_minutes=0):
    conn = _get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO tasks (title, description, deadline, estimated_minutes, created_at, reminder_minutes) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, deadline, estimated_minutes, now, reminder_minutes),
    )
    conn.commit()
    conn.close()


def update_task(task_id, **kwargs):
    if not kwargs:
        return
    conn = _get_conn()
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]
    conn.execute(f"UPDATE tasks SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = _get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def get_task(task_id):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tasks(status=None, sort_by="created_at", sort_desc=False):
    conn = _get_conn()
    valid_sorts = {"created_at", "deadline", "elapsed_seconds", "title", "status"}
    if sort_by not in valid_sorts:
        sort_by = "created_at"
    order = "DESC" if sort_desc else "ASC"
    if status and status != "all":
        rows = conn.execute(
            f"SELECT * FROM tasks WHERE status=? ORDER BY {sort_by} {order}",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM tasks ORDER BY {sort_by} {order}"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_running_task():
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM tasks WHERE timer_started_at IS NOT NULL"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def start_timer(task_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_task(task_id, status="in_progress", timer_started_at=now)


def pause_timer(task_id):
    task = get_task(task_id)
    if not task or not task["timer_started_at"]:
        return
    started = datetime.strptime(task["timer_started_at"], "%Y-%m-%d %H:%M:%S")
    elapsed = int((datetime.now() - started).total_seconds())
    update_task(
        task_id,
        elapsed_seconds=task["elapsed_seconds"] + elapsed,
        timer_started_at=None,
    )


def stop_timer(task_id):
    task = get_task(task_id)
    if not task:
        return
    if task["timer_started_at"]:
        started = datetime.strptime(task["timer_started_at"], "%Y-%m-%d %H:%M:%S")
        elapsed = int((datetime.now() - started).total_seconds())
        update_task(
            task_id,
            elapsed_seconds=task["elapsed_seconds"] + elapsed,
            timer_started_at=None,
        )


def get_stats():
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='pending'"
    ).fetchone()[0]
    in_progress = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='in_progress'"
    ).fetchone()[0]
    done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='done'"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "in_progress": in_progress, "done": done}


def cleanup_old_tasks(days=30):
    conn = _get_conn()
    threshold = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "DELETE FROM tasks WHERE status='done' AND created_at < datetime(?, ?)",
        (threshold, f"-{days} days"),
    )
    count = conn.total_changes
    conn.commit()
    conn.close()
    return count


def get_pending_reminders():
    conn = _get_conn()
    rows = conn.execute(
        """SELECT * FROM tasks
           WHERE status IN ('pending', 'in_progress')
             AND deadline IS NOT NULL
             AND reminder_minutes > 0
             AND reminder_fired = 0
             AND datetime('now', 'localtime', '+' || reminder_minutes || ' minutes') >= datetime(deadline)
           ORDER BY deadline ASC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_reminder_fired(task_id):
    update_task(task_id, reminder_fired=1)


def vacuum_db():
    conn = _get_conn()
    conn.execute("VACUUM")
    conn.close()
