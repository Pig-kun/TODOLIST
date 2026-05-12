import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

FONT_NORMAL = ("Microsoft YaHei UI", 10)
FONT_BOLD = ("Microsoft YaHei UI", 10, "bold")
FONT_TITLE = ("Microsoft YaHei UI", 14, "bold")
PAD = {"padx": 6, "pady": 4}


def format_seconds(total_seconds):
    if total_seconds <= 0:
        return "00:00:00"
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _days_in_month(year, month):
    if month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    return 31 if month in (1, 3, 5, 7, 8, 10, 12) else 30


# ---------- DateTimePicker ----------

class DateTimePicker(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        now = datetime.now()

        self._year_var = tk.StringVar(value=str(now.year))
        self._month_var = tk.StringVar(value=f"{now.month:02d}")
        self._day_var = tk.StringVar(value=f"{now.day:02d}")
        self._hour_var = tk.StringVar(value=f"{now.hour:02d}")
        self._minute_var = tk.StringVar(value=f"{now.minute:02d}")

        years = [str(y) for y in range(now.year, now.year + 11)]
        months = [f"{m:02d}" for m in range(1, 13)]
        hours = [f"{h:02d}" for h in range(0, 24)]
        minutes = [f"{m:02d}" for m in range(0, 60)]

        self._cb_year = ttk.Combobox(self, textvariable=self._year_var, values=years, state="readonly", width=5)
        self._cb_year.pack(side=tk.LEFT)
        ttk.Label(self, text="年", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(1, 4))

        self._cb_month = ttk.Combobox(self, textvariable=self._month_var, values=months, state="readonly", width=3)
        self._cb_month.pack(side=tk.LEFT)
        ttk.Label(self, text="月", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(1, 4))

        self._cb_day = ttk.Combobox(self, textvariable=self._day_var, state="readonly", width=3)
        self._cb_day.pack(side=tk.LEFT)
        ttk.Label(self, text="日", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(1, 6))

        self._cb_hour = ttk.Combobox(self, textvariable=self._hour_var, values=hours, state="readonly", width=3)
        self._cb_hour.pack(side=tk.LEFT)
        ttk.Label(self, text="时", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(1, 4))

        self._cb_minute = ttk.Combobox(self, textvariable=self._minute_var, values=minutes, state="readonly", width=3)
        self._cb_minute.pack(side=tk.LEFT)
        ttk.Label(self, text="分", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(1, 4))

        self._cb_year.bind("<<ComboboxSelected>>", self._on_ym_change)
        self._cb_month.bind("<<ComboboxSelected>>", self._on_ym_change)
        self._refresh_days()

    def _on_ym_change(self, event=None):
        self._refresh_days()

    def _refresh_days(self):
        try:
            year = int(self._year_var.get())
            month = int(self._month_var.get())
        except ValueError:
            return
        max_day = _days_in_month(year, month)
        days = [f"{d:02d}" for d in range(1, max_day + 1)]
        cur = self._day_var.get()
        self._cb_day["values"] = days
        if cur not in days:
            self._day_var.set(days[-1])

    def get(self):
        return f"{self._year_var.get()}-{self._month_var.get()}-{self._day_var.get()} {self._hour_var.get()}:{self._minute_var.get()}"

    def set(self, value):
        if not value:
            return
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                dt = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return
        self._year_var.set(str(dt.year))
        self._month_var.set(f"{dt.month:02d}")
        self._day_var.set(f"{dt.day:02d}")
        self._hour_var.set(f"{dt.hour:02d}")
        self._minute_var.set(f"{dt.minute:02d}")
        self._refresh_days()


# ---------- Dialogs ----------

class TaskDialog(tk.Toplevel):
    def __init__(self, parent, task=None):
        super().__init__(parent)
        self.result = None
        is_edit = task is not None
        self.title("编辑任务" if is_edit else "新增任务")
        self.geometry("420x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="任务名称 *", font=FONT_BOLD).pack(anchor=tk.W, **PAD)
        self.title_var = tk.StringVar(value=task["title"] if is_edit else "")
        ttk.Entry(frame, textvariable=self.title_var, width=50).pack(fill=tk.X, **PAD)

        ttk.Label(frame, text="描述", font=FONT_BOLD).pack(anchor=tk.W, **PAD)
        self.desc_text = tk.Text(frame, height=4, width=50, font=FONT_NORMAL)
        self.desc_text.pack(fill=tk.X, **PAD)
        if is_edit and task.get("description"):
            self.desc_text.insert("1.0", task["description"])

        ttk.Label(frame, text="截止时间", font=FONT_BOLD).pack(anchor=tk.W, **PAD)
        self.dt_picker = DateTimePicker(frame)
        self.dt_picker.pack(anchor=tk.W, **PAD)
        if is_edit and task.get("deadline"):
            self.dt_picker.set(task["deadline"])

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, **PAD)
        ttk.Label(row2, text="预计用时(分钟)", font=FONT_BOLD).pack(side=tk.LEFT)
        self.est_var = tk.StringVar(value=str(task["estimated_minutes"]) if (is_edit and task.get("estimated_minutes")) else "0")
        ttk.Spinbox(row2, textvariable=self.est_var, from_=0, to=9999, width=6).pack(side=tk.LEFT, padx=6)

        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, **PAD)
        self.reminder_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(row3, text="开启倒计时提醒，提前", variable=self.reminder_enabled).pack(side=tk.LEFT)
        self.reminder_var = tk.StringVar(value="15")
        ttk.Spinbox(row3, textvariable=self.reminder_var, from_=1, to=1440, width=4).pack(side=tk.LEFT)
        ttk.Label(row3, text="分钟弹窗", font=FONT_NORMAL).pack(side=tk.LEFT)
        if is_edit and task.get("reminder_minutes", 0) > 0:
            self.reminder_enabled.set(True)
            self.reminder_var.set(str(task["reminder_minutes"]))

        btn_row = ttk.Frame(frame)
        btn_row.pack(pady=12)
        ttk.Button(btn_row, text="保存", command=self._on_save, width=10).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="取消", command=self._on_cancel, width=10).pack(side=tk.LEFT, padx=6)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("提示", "任务名称不能为空。", parent=self)
            return
        self.result = {
            "title": title,
            "description": self.desc_text.get("1.0", tk.END).strip(),
            "deadline": self.dt_picker.get(),
            "estimated_minutes": int(self.est_var.get() or 0),
            "reminder_minutes": int(self.reminder_var.get() or 15) if self.reminder_enabled.get() else 0,
        }
        self.destroy()

    def _on_cancel(self):
        self.destroy()


class CleanupDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("清理缓存")
        self.geometry("340x160")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="删除多少天前已完成的任务？", font=FONT_NORMAL).pack(anchor=tk.W, **PAD)
        self.days_var = tk.StringVar(value="30")
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, **PAD)
        ttk.Spinbox(row, textvariable=self.days_var, from_=1, to=365, width=6).pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="天", font=FONT_NORMAL).pack(side=tk.LEFT)

        ttk.Label(frame, text="清理后还会压缩数据库以释放空间。", font=("Microsoft YaHei UI", 8), foreground="gray").pack(anchor=tk.W, **PAD)

        btn_row = ttk.Frame(frame)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="执行清理", command=self._on_clean, width=10).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="取消", command=self._on_cancel, width=10).pack(side=tk.LEFT, padx=6)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_clean(self):
        self.result = int(self.days_var.get() or 30)
        self.destroy()

    def _on_cancel(self):
        self.destroy()


# ---------- Main Window ----------

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TODO 任务管理器")
        self.root.geometry("860x560")
        self.root.minsize(640, 400)

        self._build_menu()
        self._build_toolbar()
        self._build_task_list()
        self._build_timer_bar()
        self._build_status_bar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- Menu ---

    def _build_menu(self):
        menubar = tk.Menu(self.root, font=FONT_NORMAL)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, font=FONT_NORMAL)
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="文件", menu=file_menu)

        task_menu = tk.Menu(menubar, tearoff=0, font=FONT_NORMAL)
        task_menu.add_command(label="新增任务", accelerator="Ctrl+N")
        task_menu.add_command(label="编辑任务", accelerator="Ctrl+E")
        task_menu.add_command(label="删除任务", accelerator="Delete")
        task_menu.add_separator()
        task_menu.add_command(label="开始计时", accelerator="Ctrl+T")
        task_menu.add_command(label="暂停计时", accelerator="Ctrl+P")
        task_menu.add_command(label="完成任务", accelerator="Ctrl+D")
        menubar.add_cascade(label="任务", menu=task_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, font=FONT_NORMAL)
        tools_menu.add_command(label="清理缓存")
        menubar.add_cascade(label="工具", menu=tools_menu)

        self.menu_task = task_menu
        self.menu_tools = tools_menu

    # --- Toolbar ---

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=4)
        toolbar.pack(fill=tk.X, padx=4, pady=(4, 0))

        self.btn_add = ttk.Button(toolbar, text="新增任务", width=9)
        self.btn_add.pack(side=tk.LEFT, padx=2)
        self.btn_timer = ttk.Button(toolbar, text="开始计时", width=9)
        self.btn_timer.pack(side=tk.LEFT, padx=2)
        self.btn_pause = ttk.Button(toolbar, text="暂停计时", width=9, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        self.btn_done = ttk.Button(toolbar, text="完成任务", width=9)
        self.btn_done.pack(side=tk.LEFT, padx=2)
        self.btn_delete = ttk.Button(toolbar, text="删除任务", width=9)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)

        ttk.Label(toolbar, text="筛选:", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(2, 2))
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(
            toolbar, textvariable=self.filter_var, values=["全部", "待办", "进行中", "已完成"],
            state="readonly", width=8
        )
        filter_combo.pack(side=tk.LEFT, padx=2)
        self.filter_combo = filter_combo

        ttk.Label(toolbar, text="排序:", font=FONT_NORMAL).pack(side=tk.LEFT, padx=(8, 2))
        self.sort_var = tk.StringVar(value="创建时间")
        sort_combo = ttk.Combobox(
            toolbar, textvariable=self.sort_var,
            values=["创建时间", "截止日期", "用时", "名称"],
            state="readonly", width=10
        )
        sort_combo.pack(side=tk.LEFT, padx=2)
        self.sort_combo = sort_combo

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        self.btn_clean = ttk.Button(toolbar, text="清理缓存", width=9)
        self.btn_clean.pack(side=tk.LEFT, padx=2)

    # --- Task List ---

    def _build_task_list(self):
        list_frame = ttk.Frame(self.root, padding=4)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        columns = ("status", "title", "deadline", "elapsed", "created_at")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings",
            selectmode="browse", height=14
        )

        self.tree.heading("status", text="状态")
        self.tree.column("status", width=50, anchor=tk.CENTER, stretch=False)
        self.tree.heading("title", text="任务名称")
        self.tree.column("title", width=260, stretch=True)
        self.tree.heading("deadline", text="截止时间")
        self.tree.column("deadline", width=140, anchor=tk.CENTER, stretch=False)
        self.tree.heading("elapsed", text="用时")
        self.tree.column("elapsed", width=70, anchor=tk.CENTER, stretch=False)
        self.tree.heading("created_at", text="创建时间")
        self.tree.column("created_at", width=130, anchor=tk.CENTER, stretch=False)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("done", foreground="gray", font=("Microsoft YaHei UI", 10, "overstrike"))
        self.tree.tag_configure("in_progress", foreground="#1a73e8")

        self._status_map = {"pending": "⬜", "in_progress": "▶", "done": "✅"}

    # --- Timer Bar ---

    def _build_timer_bar(self):
        self.timer_frame = ttk.Frame(self.root, padding=4)
        self.timer_frame.pack(fill=tk.X, padx=4)
        ttk.Separator(self.timer_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 4))
        self.timer_label = ttk.Label(self.timer_frame, text="⏱ 未开始计时", font=FONT_NORMAL)
        self.timer_label.pack(side=tk.LEFT, padx=4)

    # --- Status Bar ---

    def _build_status_bar(self):
        status_frame = ttk.Frame(self.root, padding=2)
        status_frame.pack(fill=tk.X, padx=4, pady=(0, 2))
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 2))
        self.status_label = ttk.Label(status_frame, text="就绪", font=("Microsoft YaHei UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=4)

    # --- Public methods for controller ---

    def refresh_list(self, tasks):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for t in tasks:
            elapsed_str = format_seconds(t["elapsed_seconds"])
            deadline_str = t.get("_deadline_display", "")
            created_str = t["created_at"][:16] if t["created_at"] else ""
            status_icon = self._status_map.get(t["status"], "⬜")
            values = (status_icon, t["title"], deadline_str, elapsed_str, created_str)
            tags = []
            if t["status"] == "done":
                tags.append("done")
            elif t["status"] == "in_progress":
                tags.append("in_progress")
            self.tree.insert("", tk.END, iid=str(t["id"]), values=values, tags=tags)

    def get_selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def select_task(self, task_id):
        children = self.tree.get_children()
        tid = str(task_id)
        if tid not in children:
            return
        self.tree.selection_set(tid)
        self.tree.focus(tid)
        self.tree.see(tid)

    def set_timer_running(self, task_title, elapsed_str):
        self.timer_label.config(text=f"⏱ 正在计时: {task_title}  |  已用时: {elapsed_str}")
        self.btn_timer.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)

    def set_timer_paused(self):
        self.timer_label.config(text=f"⏱ 计时已暂停")
        self.btn_timer.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)

    def set_timer_idle(self):
        self.timer_label.config(text="⏱ 未开始计时")
        self.btn_timer.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)

    def update_status_bar(self, stats):
        parts = [
            f"共 {stats['total']} 个任务",
            f"待办: {stats['pending']}",
            f"进行中: {stats['in_progress']}",
            f"已完成: {stats['done']}",
        ]
        self.status_label.config(text="  |  ".join(parts))

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message, parent=self.root)

    def ask_yes_no(self, title, message):
        return messagebox.askyesno(title, message, parent=self.root)

    def run(self):
        self.root.mainloop()

    def _on_close(self):
        self.root.quit()
