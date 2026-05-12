from datetime import datetime, timedelta, date
import models
from views import format_seconds

STATUS_NAMES = {"all": "全部", "pending": "待办", "in_progress": "进行中", "done": "已完成"}
SORT_NAMES = {"created_at": "创建时间", "deadline": "截止日期", "elapsed_seconds": "用时", "title": "名称"}
STATUS_MAP = {v: k for k, v in STATUS_NAMES.items()}
SORT_MAP = {v: k for k, v in SORT_NAMES.items()}
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class AppController:
    def __init__(self, view):
        self.view = view
        self._timer_task_id = None
        self._timer_after_id = None
        self._timer_elapsed_base = 0
        self._timer_started_at = None

        self._bind_events()
        models.init_db()
        self._resume_timer_from_db()
        self._refresh()
        self._setup_keyboard()
        self.view.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_reminder_check()

    # ---------- Event binding ----------

    def _bind_events(self):
        v = self.view
        v.btn_add.config(command=self.add_task)
        v.btn_timer.config(command=self.start_timer)
        v.btn_pause.config(command=self.pause_timer)
        v.btn_done.config(command=self.complete_task)
        v.btn_delete.config(command=self.delete_task)
        v.btn_clean.config(command=self.clean_cache)
        v.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        v.sort_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        v.tree.bind("<Double-1>", lambda e: self.edit_task())
        v.menu_task.entryconfigure(0, command=self.add_task)
        v.menu_task.entryconfigure(1, command=self.edit_task)
        v.menu_task.entryconfigure(2, command=self.delete_task)
        v.menu_task.entryconfigure(4, command=self.start_timer)
        v.menu_task.entryconfigure(5, command=self.pause_timer)
        v.menu_task.entryconfigure(6, command=self.complete_task)
        v.menu_tools.entryconfigure(0, command=self.clean_cache)

    def _setup_keyboard(self):
        root = self.view.root
        root.bind("<Control-n>", lambda e: self.add_task())
        root.bind("<Control-e>", lambda e: self.edit_task())
        root.bind("<Control-t>", lambda e: self.start_timer())
        root.bind("<Control-p>", lambda e: self.pause_timer())
        root.bind("<Control-d>", lambda e: self.complete_task())
        root.bind("<Delete>", lambda e: self.delete_task())
        root.bind("<Control-q>", lambda e: root.quit())

    def _on_close(self):
        self._pause_running_timer()
        self.view.root.quit()

    # ---------- Timer ----------

    def _resume_timer_from_db(self):
        task = models.get_running_task()
        if task:
            self._timer_task_id = task["id"]
            self._timer_elapsed_base = task["elapsed_seconds"]
            self._timer_started_at = datetime.strptime(task["timer_started_at"], "%Y-%m-%d %H:%M:%S")
            self._start_tick()

    def _start_tick(self):
        self._tick()
        self._timer_after_id = self.view.root.after(1000, self._start_tick)

    def _stop_tick(self):
        if self._timer_after_id:
            self.view.root.after_cancel(self._timer_after_id)
            self._timer_after_id = None

    def _tick(self):
        if self._timer_task_id is None:
            return
        now = datetime.now()
        extra = int((now - self._timer_started_at).total_seconds()) if self._timer_started_at else 0
        total = self._timer_elapsed_base + extra
        task = models.get_task(self._timer_task_id)
        title = task["title"] if task else "?"
        self.view.set_timer_running(title, format_seconds(total))

    def _pause_running_timer(self):
        if self._timer_task_id is not None:
            models.pause_timer(self._timer_task_id)
            task = models.get_task(self._timer_task_id)
            if task:
                self._timer_elapsed_base = task["elapsed_seconds"]
            self._timer_task_id = None
            self._timer_started_at = None
            self._stop_tick()
            self.view.set_timer_paused()

    def start_timer(self):
        task_id = self.view.get_selected_id()
        if task_id is None:
            self.view.show_warning("提示", "请先选择一个任务。")
            return
        task = models.get_task(task_id)
        if task["status"] == "done":
            self.view.show_warning("提示", "已完成的任务不能计时。")
            return

        self._pause_running_timer()

        models.start_timer(task_id)
        task = models.get_task(task_id)
        self._timer_task_id = task_id
        self._timer_elapsed_base = task["elapsed_seconds"]
        self._timer_started_at = datetime.strptime(task["timer_started_at"], "%Y-%m-%d %H:%M:%S")
        self._start_tick()
        self._refresh()

    def pause_timer(self):
        if self._timer_task_id is None:
            self.view.show_warning("提示", "当前没有正在计时的任务。")
            return
        self._pause_running_timer()
        self.view.set_timer_idle()
        self._refresh()

    # ---------- Reminder ----------

    def _start_reminder_check(self):
        self._check_reminders()

    def _check_reminders(self):
        reminders = models.get_pending_reminders()
        for task in reminders:
            dl = task["deadline"]
            models.mark_reminder_fired(task["id"])
            self.view.show_info(
                "倒计时提醒",
                f"任务「{task['title']}」的截止时间即将到达！\n\n截止时间: {dl}",
            )
        self.view.root.after(30000, self._check_reminders)

    # ---------- Task CRUD ----------

    def add_task(self):
        dialog_result = self._show_task_dialog()
        if dialog_result is None:
            return
        models.add_task(**dialog_result)
        self._refresh()

    def edit_task(self):
        task_id = self.view.get_selected_id()
        if task_id is None:
            self.view.show_warning("提示", "请先选择一个任务。")
            return
        task = models.get_task(task_id)
        dialog_result = self._show_task_dialog(task)
        if dialog_result is None:
            return
        dialog_result["reminder_fired"] = 0
        models.update_task(task_id, **dialog_result)
        self._refresh()

    def delete_task(self):
        task_id = self.view.get_selected_id()
        if task_id is None:
            self.view.show_warning("提示", "请先选择一个任务。")
            return
        task = models.get_task(task_id)
        if not self.view.ask_yes_no("确认删除", f"确定要删除任务「{task['title']}」吗？"):
            return
        if task_id == self._timer_task_id:
            self._pause_running_timer()
            self.view.set_timer_idle()
        models.delete_task(task_id)
        self._refresh()

    def complete_task(self):
        task_id = self.view.get_selected_id()
        if task_id is None:
            self.view.show_warning("提示", "请先选择一个任务。")
            return
        if task_id == self._timer_task_id:
            self._pause_running_timer()
            self.view.set_timer_idle()
        models.stop_timer(task_id)
        models.update_task(task_id, status="done")
        self._refresh()

    # ---------- Cache clean ----------

    def clean_cache(self):
        from views import CleanupDialog
        dlg = CleanupDialog(self.view.root)
        self.view.root.wait_window(dlg)
        if dlg.result is None:
            return
        days = dlg.result
        count = models.cleanup_old_tasks(days)
        models.vacuum_db()
        self._refresh()
        self.view.show_info("清理完成", f"已删除 {count} 个 {days} 天前完成的任务，数据库已压缩。")

    # ---------- Internal ----------

    def _show_task_dialog(self, task=None):
        from views import TaskDialog
        dlg = TaskDialog(self.view.root, task)
        self.view.root.wait_window(dlg)
        return dlg.result

    def _format_deadline(self, task):
        dl = task.get("deadline")
        if not dl:
            return ""
        try:
            dl_dt = datetime.strptime(dl, "%Y-%m-%d %H:%M")
        except ValueError:
            return dl
        wd = WEEKDAYS[dl_dt.weekday()]
        disp = dl_dt.strftime(f"%m-%d {wd} %H:%M")
        if task["status"] == "done":
            return disp
        now = datetime.now()
        diff = dl_dt - now
        secs = diff.total_seconds()
        if secs < 0:
            total_min = int(abs(secs) // 60)
            task.setdefault("_tags", []).append("overdue")
            if total_min < 60:
                return f"{disp}\n超时{total_min}分"
            elif total_min < 1440:
                return f"{disp}\n超时{total_min // 60}时"
            else:
                return f"{disp}\n超时{total_min // 1440}天"
        else:
            total_min = int(secs // 60)
            if total_min < 60:
                return f"{disp}\n剩{total_min}分"
            elif total_min < 1440:
                return f"{disp}\n剩{total_min // 60}时"
            else:
                return f"{disp}\n剩{total_min // 1440}天"

    def _group_key(self, task):
        dl = task.get("deadline")
        if not dl:
            return "none"
        try:
            dl_dt = datetime.strptime(dl, "%Y-%m-%d %H:%M")
        except ValueError:
            return "none"
        today = date.today()
        dl_date = dl_dt.date()
        if dl_date == today:
            return "today"
        elif dl_date == today + timedelta(days=1):
            return "tomorrow"
        else:
            return dl_date.isoformat()

    def _group_label(self, key):
        if key == "today":
            today = date.today()
            return f"今天 {today:%m-%d} ({WEEKDAYS[today.weekday()]})"
        elif key == "tomorrow":
            tmr = date.today() + timedelta(days=1)
            return f"明天 {tmr:%m-%d} ({WEEKDAYS[tmr.weekday()]})"
        elif key == "none":
            return "无截止日期"
        else:
            try:
                dt = date.fromisoformat(key)
                return f"{dt:%m-%d} ({WEEKDAYS[dt.weekday()]})"
            except ValueError:
                return key

    def _refresh(self):
        status_cn = self.view.filter_var.get()
        sort_cn = self.view.sort_var.get()
        status = STATUS_MAP.get(status_cn, "all")
        sort_by = SORT_MAP.get(sort_cn, "created_at")
        tasks = models.get_tasks(status=status, sort_by=sort_by)
        for t in tasks:
            t["_tags"] = []
            if t["status"] == "done":
                t["_tags"].append("done")
            elif t["status"] == "in_progress":
                t["_tags"].append("in_progress")
            t["_deadline_display"] = self._format_deadline(t)

        grouped = {}
        order = []
        for t in tasks:
            key = self._group_key(t)
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(t)

        def _key_sort(k):
            if k == "today":
                return (0, "")
            elif k == "tomorrow":
                return (1, "")
            elif k == "none":
                return (99, "")
            else:
                return (2, k)

        order.sort(key=_key_sort)

        groups = [{"id": f"grp_{k}", "key": k, "label": self._group_label(k), "tasks": grouped[k]} for k in order if grouped[k]]
        self.view.refresh_list(groups)
        stats = models.get_stats()
        self.view.update_status_bar(stats)
