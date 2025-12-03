# visual_tasks.py
"""
Fully Integrated Task Visualizer
- ThreadPool execution
- CPU / IO / Mixed tasks
- Green striped progress bars + glow effect
- Final progress update guaranteed (100% filled)
- System metrics integration
- Task cancellation
- Light / Dark mode
"""

import tkinter as tk
from tkinter import ttk
import random
import time
from core_engine import ThreadPool
from monitoring import Monitor

try:
    import psutil
except:
    psutil = None


class TaskVisualizer:
    def __init__(self, pool: ThreadPool):
        self.pool = pool
        self.monitor = Monitor(pool)
        self.task_counter = 0
        self.cancel_flags = {}

        # ---------------- WINDOW ----------------
        self.root = tk.Tk()
        self.root.title("ThreadPool Task Manager")
        self.root.geometry("1150x780")

        # Theme
        self.base_font = ("Segoe UI", 10)
        self.root.option_add("*Font", self.base_font)
        self.style = ttk.Style(self.root)
        self._current_theme = "light"
        self.configure_theme()
        self.configure_progressbar_styles()

        # ---------------- HEADER ----------------
        top_bar = tk.Frame(self.root, bg=self.bg_main)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar, text="⚙️ ThreadPool Task Manager",
            bg=self.bg_main, fg=self.fg_main,
            font=("Segoe UI Semibold", 18)
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # Dark mode
        self.dark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top_bar,
            text="Dark Mode",
            variable=self.dark_var,
            command=self.toggle_theme
        ).pack(side=tk.RIGHT, padx=20)

        # Heartbeat
        self.pulse_lbl = tk.Label(
            top_bar, text="●", fg="#2ecc71",
            bg=self.bg_main, font=("Segoe UI", 18)
        )
        self.pulse_lbl.pack(side=tk.RIGHT, padx=10)
        self.pulse_state = True

        # ---------------- MAIN SPLIT ----------------
        main_frame = tk.Frame(self.root, bg=self.bg_main)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame, bg=self.bg_main)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main_frame, bg=self.bg_main)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # ---------------- FORM ----------------
        form_frame = ttk.LabelFrame(left_frame, text="Create New Task")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, padx=8, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=18)
        self.name_entry.grid(row=0, column=1)

        ttk.Label(form_frame, text="Duration (s):").grid(row=0, column=2, padx=8)
        self.duration_spin = ttk.Spinbox(form_frame, from_=1, to=15, width=6)
        self.duration_spin.set(5)
        self.duration_spin.grid(row=0, column=3)

        ttk.Label(form_frame, text="Type:").grid(row=1, column=0)
        self.task_type = tk.StringVar(value="CPU-bound")
        ttk.Combobox(
            form_frame, textvariable=self.task_type,
            values=["CPU-bound", "IO-bound", "Mixed"],
            width=14, state="readonly"
        ).grid(row=1, column=1)

        ttk.Label(form_frame, text="Priority:").grid(row=1, column=2)
        self.priority = tk.StringVar(value="Medium")

        prio_frame = tk.Frame(form_frame, bg=self.bg_main)
        prio_frame.grid(row=1, column=3)
        for p in ["Low", "Medium", "High"]:
            ttk.Radiobutton(prio_frame, text=p, value=p,
                            variable=self.priority).pack(side=tk.LEFT)

        self.critical_flag = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="⚡ Critical",
                        variable=self.critical_flag).grid(row=0, column=4)

        ttk.Button(form_frame, text="➕ Add Task",
                   command=self.add_manual_task).grid(row=1, column=4, padx=5)
        ttk.Button(form_frame, text="🚫 Cancel Selected",
                   command=self.cancel_selected_task).grid(row=2, column=4, padx=5, pady=5)

        # ---------------- QUICK ACTIONS ----------------
        quick_frame = ttk.LabelFrame(left_frame, text="Quick Actions")
        quick_frame.pack(fill=tk.X, padx=10)

        ttk.Button(
            quick_frame, text="🎲 Generate Random Tasks",
            command=self.add_random_tasks
        ).pack(side=tk.LEFT, padx=10, pady=8)

        ttk.Button(
            quick_frame, text="🧹 Clear Logs",
            command=lambda: self.log_box.delete("1.0", tk.END)
        ).pack(side=tk.LEFT, padx=10)

        # ---------------- TASK TABLE ----------------
        table_frame = ttk.LabelFrame(left_frame, text="Task Status")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("task", "status", "type", "priority", "progress")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        for col in columns:
            self.tree.heading(col, text=col.capitalize())

        self.tree.column("task", width=130)
        self.tree.column("status", width=140)
        self.tree.column("type", width=130)
        self.tree.column("priority", width=100)
        self.tree.column("progress", width=260)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.rows = {}
        self.progress_bars = {}

        # ---------------- LOGS ----------------
        log_frame = ttk.LabelFrame(left_frame, text="Logs")
        log_frame.pack(fill=tk.X, padx=10)
        self.log_box = tk.Text(log_frame, height=6)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        # ---------------- METRICS PANEL ----------------
        metrics_frame = ttk.LabelFrame(right_frame, text="System Metrics")
        metrics_frame.pack(fill=tk.Y, padx=10, pady=10)

        metric_keys = [
            "tasks_submitted", "tasks_completed",
            "tasks_failed", "queue_length",
            "active_workers", "cpu_percent",
            "memory_usage_mb"
        ]
        self.metrics_labels = {}
        for key in metric_keys:
            lbl = ttk.Label(metrics_frame, text=f"{key}: 0")
            lbl.pack(anchor="w", padx=10, pady=6)
            self.metrics_labels[key] = lbl

        # LOOP
        self.root.after(200, self.update_ui)
        self.root.bind("<Configure>", lambda e: self.update_positions())

    # ---------------- THEME ----------------
    def configure_theme(self):
        if self._current_theme == "light":
            self.bg_main = "#F2F2F2"
            self.fg_main = "#1E1E1E"
        else:
            self.bg_main = "#1E1E1E"
            self.fg_main = "#F2F2F2"

        self.root.configure(bg=self.bg_main)
        self.style.theme_use("clam")
        self.style.configure(
            ".", background=self.bg_main,
            foreground=self.fg_main,
            fieldbackground=self.bg_main
        )

    # ---------------- PROGRESSBAR STYLES ----------------
    def configure_progressbar_styles(self):
        self.style.configure(
            "Striped.Green.Horizontal.TProgressbar",
            troughcolor=self.bg_main,
            background="#00cc44",
        )
        self.style.configure(
            "Glow.Horizontal.TProgressbar",
            troughcolor=self.bg_main,
            background="#7CFCAC"
        )

    # ---------------- CREATE TASK ----------------
    def add_manual_task(self):
        name = self.name_entry.get().strip() or f"Task-{self.task_counter + 1}"
        duration = int(self.duration_spin.get())
        ttype = self.task_type.get()

        prio_map = {"Low": 1, "Medium": 2, "High": 3}
        prio = prio_map[self.priority.get()]
        if self.critical_flag.get():
            prio += 2

        self.create_task(name, duration, ttype, prio)

    def add_random_tasks(self):
        for _ in range(3):
            tid = f"Task-{self.task_counter + 1}"
            self.create_task(
                tid,
                random.randint(2, 6),
                random.choice(["CPU-bound", "IO-bound", "Mixed"]),
                random.randint(1, 3)
            )

    def create_task(self, tid, duration, ttype, priority):
        self.task_counter += 1

        row = self.tree.insert(
            "", tk.END,
            values=(tid, f"Waiting ({duration}s)", ttype, priority, "0%")
        )
        self.rows[tid] = row
        self.cancel_flags[tid] = False

        pb = ttk.Progressbar(
            self.root, maximum=100,
            style="Striped.Green.Horizontal.TProgressbar"
        )
        self.progress_bars[tid] = pb
        self.place_progress_bar(tid)

        self.pool.submit(self.run_task, tid, duration, ttype, priority)
        self.log(f"{tid} submitted")

    # ---------------- CANCEL TASK ----------------
    def cancel_selected_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        row = sel[0]
        tid = self.tree.item(row, "values")[0]
        self.cancel_flags[tid] = True
        self.tree.set(row, "status", "CANCELLING")
        self.log(f"{tid} cancellation requested")

    # ---------------- SAFE SLEEP ----------------
    def _safe_sleep(self, t):
        end = time.time() + t
        while time.time() < end:
            self.root.update_idletasks()
            time.sleep(0.01)

    # ---------------- RUN TASK ----------------
    def run_task(self, tid, duration, ttype, priority):
        row = self.rows[tid]
        self.tree.set(row, "status", "RUNNING")

        steps = 50
        for i in range(steps + 1):

            if self.cancel_flags[tid]:
                self.tree.set(row, "status", "CANCELLED")
                self.tree.set(row, "progress", "Cancelled")
                return

            pct = int(i / steps * 100)
            self.progress_bars[tid]["value"] = pct
            self.tree.set(row, "progress", f"{pct}%")
            self.place_progress_bar(tid)

            # Execution simulation
            if ttype == "CPU-bound":
                _ = sum(j*j for j in range(6000))
            elif ttype == "IO-bound":
                self._safe_sleep(duration / steps)
            else:  # Mixed
                if i % 2 == 0:
                    _ = sum(j*j for j in range(3000))
                self._safe_sleep((duration / steps) / 2)

        # ------ GUARANTEED FINAL 100% UPDATE ------
        self.root.after(10, lambda tid=tid: self.finish_progress_bar(tid))

        self.tree.set(row, "status", "COMPLETED")
        self.log(f"{tid} finished")

    # ---------------- FINAL PROGRESS FIX ----------------
    def finish_progress_bar(self, tid):
        """Ensures progress bar completes fully and glows."""
        if tid in self.progress_bars:
            pb = self.progress_bars[tid]
            pb["value"] = 100
            pb.config(style="Glow.Horizontal.TProgressbar")
            self.place_progress_bar(tid)

    # ---------------- PLACE PROGRESSBAR ----------------
    def place_progress_bar(self, tid):
        row = self.rows[tid]
        bbox = self.tree.bbox(row, "progress")
        if not bbox:
            return

        x, y, w, h = bbox
        pb = self.progress_bars[tid]

        abs_x = self.tree.winfo_rootx() - self.root.winfo_rootx() + x
        abs_y = self.tree.winfo_rooty() - self.root.winfo_rooty() + y

        pb.place(x=abs_x, y=abs_y, width=w, height=h)

    def update_positions(self):
        for tid in self.progress_bars:
            self.place_progress_bar(tid)

    # ---------------- UI UPDATE ----------------
    def update_ui(self):

        # Heartbeat
        self.pulse_state = not self.pulse_state
        self.pulse_lbl.config(fg="#2ecc71" if self.pulse_state else "#7f8c8d")

        # Animate striped bars
        for pb in self.progress_bars.values():
            if pb["style"] == "Striped.Green.Horizontal.TProgressbar":
                pb.step(1)

        # Metrics
        stats = self.monitor.get_metrics()
        for key, lbl in self.metrics_labels.items():
            lbl.config(text=f"{key}: {stats.get(key, 0)}")

        self.root.after(200, self.update_ui)

    # ---------------- UTILITIES ----------------
    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def toggle_theme(self):
        self._current_theme = "dark" if self.dark_var.get() else "light"
        self.configure_theme()
        self.configure_progressbar_styles()
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    pool = ThreadPool(max_workers=6)
    TaskVisualizer(pool).run()
