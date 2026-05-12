import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

# ------- Palette -------
C_PRIMARY = "#4a6cf7"
C_PRIMARY_HOVER = "#3b5de7"
C_SUCCESS = "#10b981"
C_WARNING = "#f59e0b"
C_DANGER = "#ef4444"
C_BG = "#f0f2f5"
C_CARD = "#ffffff"
C_TEXT = "#1e293b"
C_TEXT_SEC = "#64748b"
C_BORDER = "#e2e8f0"
C_GROUP = "#eef2ff"
C_GROUP_FG = "#3730a3"
C_ROW_ODD = "#ffffff"
C_ROW_EVEN = "#f8fafc"
C_PROGRESS = "#2563eb"
C_DONE = "#94a3b8"
C_OVERDUE = "#dc2626"
C_TIMER_BG = "#fefce8"
C_TIMER_FG = "#92400e"

FONT_NORMAL = ("Microsoft YaHei UI", 10)
FONT_BOLD = ("Microsoft YaHei UI", 10, "bold")
FONT_SMALL = ("Microsoft YaHei UI", 9)
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
        self.geometry("440x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=C_BG)

        frame = tk.Frame(self, bg=C_CARD, padx=16, pady=12, highlightbackground=C_BORDER, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tk.Label(frame, text="任务名称 *", font=FONT_BOLD, bg=C_CARD, fg=C_TEXT).pack(anchor=tk.W, **PAD)
        self.title_var = tk.StringVar(value=task["title"] if is_edit else "")
        ttk.Entry(frame, textvariable=self.title_var, width=50, font=FONT_NORMAL).pack(fill=tk.X, **PAD)

        tk.Label(frame, text="描述", font=FONT_BOLD, bg=C_CARD, fg=C_TEXT).pack(anchor=tk.W, **PAD)
        self.desc_text = tk.Text(frame, height=4, width=50, font=FONT_NORMAL, bg="#f8fafc", fg=C_TEXT,
                                 relief="solid", borderwidth=1, padx=4, pady=4)
        self.desc_text.pack(fill=tk.X, **PAD)
        if is_edit and task.get("description"):
            self.desc_text.insert("1.0", task["description"])

        tk.Label(frame, text="截止时间", font=FONT_BOLD, bg=C_CARD, fg=C_TEXT).pack(anchor=tk.W, **PAD)
        self.dt_picker = DateTimePicker(frame)
        self.dt_picker.pack(anchor=tk.W, **PAD)
        if is_edit and task.get("deadline"):
            self.dt_picker.set(task["deadline"])

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, **PAD)
        tk.Label(row2, text="预计用时(分钟)", font=FONT_BOLD, bg=C_CARD, fg=C_TEXT).pack(side=tk.LEFT)
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

        btn_row = tk.Frame(frame, bg=C_CARD)
        btn_row.pack(pady=14)
        tk.Button(btn_row, text="保存", command=self._on_save, width=10, font=FONT_BOLD,
                  bg=C_PRIMARY, fg="white", activebackground=C_PRIMARY_HOVER, activeforeground="white",
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="取消", command=self._on_cancel, width=10, font=FONT_NORMAL,
                  bg="#e2e8f0", fg=C_TEXT, activebackground="#cbd5e1", activeforeground=C_TEXT,
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side=tk.LEFT, padx=6)

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
        self.geometry("360x180")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=C_BG)

        frame = tk.Frame(self, bg=C_CARD, padx=16, pady=12, highlightbackground=C_BORDER, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tk.Label(frame, text="删除多少天前已完成的任务？", font=FONT_NORMAL, bg=C_CARD, fg=C_TEXT).pack(anchor=tk.W, **PAD)
        self.days_var = tk.StringVar(value="30")
        row = tk.Frame(frame, bg=C_CARD)
        row.pack(fill=tk.X, **PAD)
        ttk.Spinbox(row, textvariable=self.days_var, from_=1, to=365, width=6).pack(side=tk.LEFT, padx=4)
        tk.Label(row, text="天", font=FONT_NORMAL, bg=C_CARD, fg=C_TEXT).pack(side=tk.LEFT)

        tk.Label(frame, text="清理后还会压缩数据库以释放空间。", font=FONT_SMALL, bg=C_CARD, fg=C_TEXT_SEC).pack(anchor=tk.W, **PAD)

        btn_row = tk.Frame(frame, bg=C_CARD)
        btn_row.pack(pady=12)
        tk.Button(btn_row, text="执行清理", command=self._on_clean, width=10, font=FONT_BOLD,
                  bg=C_WARNING, fg="white", activebackground="#d97706", activeforeground="white",
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="取消", command=self._on_cancel, width=10, font=FONT_NORMAL,
                  bg="#e2e8f0", fg=C_TEXT, activebackground="#cbd5e1", activeforeground=C_TEXT,
                  relief="flat", cursor="hand2", padx=8, pady=3).pack(side=tk.LEFT, padx=6)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_clean(self):
        self.result = int(self.days_var.get() or 30)
        self.destroy()

    def _on_cancel(self):
        self.destroy()


# ---------- Colored Button ----------

class _ColorButton(tk.Frame):
    def __init__(self, parent, text, bg, fg="white", hover_bg=None, command=None, width=9, state="normal"):
        super().__init__(parent, bg=C_BG, highlightthickness=0)
        self._cmd = command
        self._bg = bg
        self._hover_bg = hover_bg or bg
        self._state = state
        self._btn = tk.Label(self, text=text, font=FONT_BOLD, bg=bg, fg=fg,
                             width=width, padx=4, pady=4, cursor="hand2",
                             relief="flat", anchor=tk.CENTER)
        self._btn.pack()
        if state == "normal":
            self._btn.bind("<Enter>", lambda e: self._btn.configure(bg=self._hover_bg))
            self._btn.bind("<Leave>", lambda e: self._btn.configure(bg=self._bg))
            self._btn.bind("<Button-1>", lambda e: self._cmd and self._cmd())
        else:
            self._btn.configure(bg="#cbd5e1", fg="#94a3b8", cursor="")

    def config(self, **kwargs):
        if "command" in kwargs:
            self._cmd = kwargs.pop("command")
            self._btn.bind("<Button-1>", lambda e: self._cmd and self._cmd())
        if "state" in kwargs:
            s = kwargs.pop("state")
            self._state = s
            if s == "disabled":
                self._btn.configure(bg="#cbd5e1", fg="#94a3b8", cursor="")
            else:
                self._btn.configure(bg=self._bg, fg="white", cursor="hand2")
        if "text" in kwargs:
            self._btn.configure(text=kwargs.pop("text"))
        super().config(**kwargs)


# ---------- Main Window ----------

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TODO 任务管理器")
        self.root.geometry("960x620")
        self.root.minsize(760, 480)
        self.root.configure(bg=C_BG)

        self._build_style()
        self._build_header()
        self._build_toolbar()
        self._build_task_list()
        self._build_timer_bar()
        self._build_status_bar()
        self._build_menu()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- Style ---

    def _build_style(self):
        self.root.option_add("*Font", FONT_NORMAL)
        style = ttk.Style()
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")

        style.configure(".", background=C_BG, foreground=C_TEXT, font=FONT_NORMAL)
        style.configure("Treeview", rowheight=30, font=FONT_NORMAL, background=C_CARD,
                        fieldbackground=C_CARD, borderwidth=0)
        style.configure("Treeview.Heading", font=FONT_BOLD, padding=(6, 4),
                        background=C_BG, foreground=C_TEXT_SEC, borderwidth=0)
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", C_TEXT)])
        style.map("Treeview.Heading", background=[("active", C_BG)])

        style.configure("TEntry", fieldbackground="white", borderwidth=1, relief="solid")
        style.configure("TSpinbox", fieldbackground="white", borderwidth=1, relief="solid")
        style.configure("TCombobox", fieldbackground="white", borderwidth=1, relief="solid")
        style.configure("TCheckbutton", background=C_BG)

        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("TFrame", background=C_BG)
        style.configure("TLabel", background=C_BG, foreground=C_TEXT)

    # --- Header ---

    def _build_header(self):
        header = tk.Frame(self.root, bg=C_PRIMARY, padx=16, pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="📋 TODO 任务管理器", font=("Microsoft YaHei UI", 16, "bold"),
                 bg=C_PRIMARY, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="离线 · 本地存储 · 零依赖", font=FONT_SMALL,
                 bg=C_PRIMARY, fg="#bfdbfe").pack(side=tk.RIGHT)

    # --- Toolbar ---

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=C_CARD, padx=8, pady=6,
                       highlightbackground=C_BORDER, highlightthickness=1)
        bar.pack(fill=tk.X, padx=6, pady=(6, 0))

        btn_frame = tk.Frame(bar, bg=C_CARD)
        btn_frame.pack(side=tk.LEFT)
        self.btn_add = _ColorButton(btn_frame, "＋ 新增任务", C_PRIMARY, hover_bg=C_PRIMARY_HOVER, width=10)
        self.btn_add.pack(side=tk.LEFT, padx=2)
        self.btn_timer = _ColorButton(btn_frame, "▶ 开始计时", C_SUCCESS, hover_bg="#059669", width=10)
        self.btn_timer.pack(side=tk.LEFT, padx=2)
        self.btn_pause = _ColorButton(btn_frame, "⏸ 暂停计时", C_WARNING, hover_bg="#d97706", width=10, state="disabled")
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        self.btn_done = _ColorButton(btn_frame, "✓ 完成任务", "#6366f1", hover_bg="#4f46e5", width=10)
        self.btn_done.pack(side=tk.LEFT, padx=2)
        self.btn_delete = _ColorButton(btn_frame, "✕ 删除任务", C_DANGER, hover_bg="#b91c1c", width=10)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        sep = tk.Frame(bar, bg=C_BORDER, width=1, height=24)
        sep.pack(side=tk.LEFT, padx=10)

        tk.Label(bar, text="筛选", font=FONT_SMALL, bg=C_CARD, fg=C_TEXT_SEC).pack(side=tk.LEFT, padx=(2, 2))
        self.filter_var = tk.StringVar(value="全部")
        fc = ttk.Combobox(bar, textvariable=self.filter_var,
                          values=["全部", "待办", "进行中", "已完成"],
                          state="readonly", width=8, font=FONT_SMALL)
        fc.pack(side=tk.LEFT, padx=2)
        self.filter_combo = fc

        tk.Label(bar, text="排序", font=FONT_SMALL, bg=C_CARD, fg=C_TEXT_SEC).pack(side=tk.LEFT, padx=(10, 2))
        self.sort_var = tk.StringVar(value="创建时间")
        sc = ttk.Combobox(bar, textvariable=self.sort_var,
                          values=["创建时间", "截止日期", "用时", "名称"],
                          state="readonly", width=10, font=FONT_SMALL)
        sc.pack(side=tk.LEFT, padx=2)
        self.sort_combo = sc

        sep2 = tk.Frame(bar, bg=C_BORDER, width=1, height=24)
        sep2.pack(side=tk.LEFT, padx=10)

        self.btn_clean = _ColorButton(bar, "🧹 清理缓存", "#64748b", hover_bg="#475569", width=11)
        self.btn_clean.pack(side=tk.RIGHT, padx=2)

    # --- Task List ---

    def _build_task_list(self):
        card = tk.Frame(self.root, bg=C_CARD, padx=2, pady=2,
                        highlightbackground=C_BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        columns = ("status", "title", "deadline", "elapsed", "created_at")
        self.tree = ttk.Treeview(card, columns=columns, show="tree headings",
                                 selectmode="browse", height=14,
                                 padding=(4, 2))
        self.tree.column("#0", width=210, minwidth=160, stretch=False)
        self.tree.heading("#0", text="")
        self.tree.heading("status", text="")
        self.tree.column("status", width=36, anchor=tk.CENTER, stretch=False)
        self.tree.heading("title", text="任务名称")
        self.tree.column("title", width=250, stretch=True)
        self.tree.heading("deadline", text="截止时间")
        self.tree.column("deadline", width=155, anchor=tk.CENTER, stretch=False)
        self.tree.heading("elapsed", text="用时")
        self.tree.column("elapsed", width=65, anchor=tk.CENTER, stretch=False)
        self.tree.heading("created_at", text="创建")
        self.tree.column("created_at", width=80, anchor=tk.CENTER, stretch=False)

        scrollbar = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("group", background=C_GROUP, foreground=C_GROUP_FG, font=FONT_BOLD)
        self.tree.tag_configure("done", foreground=C_DONE, font=("Microsoft YaHei UI", 10, "overstrike"))
        self.tree.tag_configure("in_progress", foreground=C_PROGRESS)
        self.tree.tag_configure("overdue", foreground=C_OVERDUE)
        self.tree.tag_configure("row_even", background=C_ROW_EVEN, foreground=C_TEXT)
        self.tree.tag_configure("row_odd", background=C_ROW_ODD, foreground=C_TEXT)

        self._status_map = {"pending": "⬜", "in_progress": "▶", "done": "✅"}

    # --- Timer Bar ---

    def _build_timer_bar(self):
        self.timer_frame = tk.Frame(self.root, bg=C_TIMER_BG, padx=10, pady=6,
                                    highlightbackground=C_BORDER, highlightthickness=1)
        self.timer_frame.pack(fill=tk.X, padx=6, pady=(2, 0))
        self.timer_label = tk.Label(self.timer_frame, text="⏱ 未开始计时", font=FONT_BOLD,
                                    bg=C_TIMER_BG, fg=C_TIMER_FG)
        self.timer_label.pack(side=tk.LEFT)

    # --- Status Bar ---

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=C_BG, padx=8, pady=4)
        bar.pack(fill=tk.X, padx=6, pady=(0, 4))
        self.status_label = tk.Label(bar, text="就绪", font=FONT_SMALL, bg=C_BG, fg=C_TEXT_SEC)
        self.status_label.pack(side=tk.LEFT)

    # --- Menu ---

    def _build_menu(self):
        menubar = tk.Menu(self.root, font=FONT_NORMAL, bg=C_CARD, fg=C_TEXT,
                          activebackground=C_PRIMARY, activeforeground="white")
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

    # --- Public methods ---

    def refresh_list(self, groups):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for g in groups:
            gid = g["id"]
            self.tree.insert("", tk.END, iid=gid, text=g["label"], tags=("group",), open=True)
            for i, t in enumerate(g["tasks"]):
                elapsed_str = format_seconds(t["elapsed_seconds"])
                deadline_str = t.get("_deadline_display", "")
                created_str = t["created_at"][5:16] if t["created_at"] else ""
                icon = self._status_map.get(t["status"], "⬜")
                values = (icon, t["title"], deadline_str, elapsed_str, created_str)
                tags = list(t.get("_tags", []))
                tags.append("row_even" if i % 2 == 0 else "row_odd")
                self.tree.insert(gid, tk.END, iid=str(t["id"]), text="", values=values, tags=tags)

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        if iid.startswith("grp_"):
            return None
        return int(iid)

    def select_task(self, task_id):
        tid = str(task_id)
        parent = self.tree.parent(tid)
        if parent:
            self.tree.item(parent, open=True)
        if not self.tree.exists(tid):
            return
        self.tree.selection_set(tid)
        self.tree.focus(tid)
        self.tree.see(tid)

    def set_timer_running(self, task_title, elapsed_str):
        self.timer_label.config(text=f"⏱ 正在计时: {task_title}  |  已用时: {elapsed_str}")
        self.timer_frame.configure(bg="#dcfce7")
        self.timer_label.configure(bg="#dcfce7", fg="#166534")
        self.btn_timer.config(state="disabled")
        self.btn_pause.config(state="normal")

    def set_timer_paused(self):
        self.timer_label.config(text="⏱ 计时已暂停")
        self.timer_frame.configure(bg=C_TIMER_BG)
        self.timer_label.configure(bg=C_TIMER_BG, fg=C_TIMER_FG)
        self.btn_timer.config(state="normal")
        self.btn_pause.config(state="disabled")

    def set_timer_idle(self):
        self.timer_label.config(text="⏱ 未开始计时")
        self.timer_frame.configure(bg=C_TIMER_BG)
        self.timer_label.configure(bg=C_TIMER_BG, fg=C_TIMER_FG)
        self.btn_timer.config(state="normal")
        self.btn_pause.config(state="disabled")

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
