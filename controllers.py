from datetime import datetime
import models
from views import format_seconds

STATUS_NAMES = {"all": "全部", "pending": "待办", "in_progress": "进行中", "done": "已完成"}
SORT_NAMES = {"created_at": "创建时间", "deadline": "截止日期", "elapsed_seconds": "用时", "title": "名称"}
STATUS_MAP = {v: k for k, v in STATUS_NAMES.items()}
SORT_MAP = {v: k for k, v in SORT_NAMES.items()}


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

    def _refresh(self):
        status_cn = self.view.filter_var.get()
        sort_cn = self.view.sort_var.get()
        status = STATUS_MAP.get(status_cn, "all")
        sort_by = SORT_MAP.get(sort_cn, "created_at")
        tasks = models.get_tasks(status=status, sort_by=sort_by)
        self.view.refresh_list(tasks)
        stats = models.get_stats()
        self.view.update_status_bar(stats)
