import tkinter as tk
from tkinter import font
import time
import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), ".pomodoro_data.json")

DURATIONS = {"pomodoro": 25, "short_break": 5, "long_break": 15}
COLORS = {"pomodoro": "#ff6b6b", "short_break": "#4ecdc4", "long_break": "#45b7d1"}
LABELS = {"pomodoro": "专注时间", "short_break": "短休息", "long_break": "长休息"}


class PomodoroTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄钟")
        self.root.geometry("360x480")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        self.mode = "pomodoro"
        self.time_left = DURATIONS[self.mode] * 60
        self.timer_id = None
        self.session_count = 0
        self.completed = self._load_count()

        self._setup_ui()
        self._update_display()
        self.root.mainloop()

    # ── data persistence ──────────────────────────────────────────

    def _load_count(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f).get("completed", 0)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return 0

    def _save_count(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"completed": self.completed}, f)

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self):
        title_font = font.Font(size=11, weight="bold")
        time_font = font.Font(size=56, weight="normal")
        label_font = font.Font(size=13)
        btn_font = font.Font(size=12, weight="bold")
        stat_font = font.Font(size=10)

        # ── tabs ──
        tab_frame = tk.Frame(self.root, bg="#1a1a2e")
        tab_frame.pack(pady=(30, 10))

        self.tabs = {}
        for key, text in [("pomodoro", "专注"), ("short_break", "短休"), ("long_break", "长休")]:
            btn = tk.Button(
                tab_frame, text=text, font=title_font,
                bg="#2a2a4a" if key == "pomodoro" else "#1a1a2e",
                fg="#eee" if key == "pomodoro" else "#666",
                relief="flat", padx=16, pady=4,
                activebackground="#3a3a5a", activeforeground="#fff",
                cursor="hand2",
                command=lambda k=key: self._switch_mode(k),
            )
            btn.pack(side=tk.LEFT, padx=4)
            self.tabs[key] = btn

        # ── canvas (timer ring) ──
        self.canvas = tk.Canvas(
            self.root, width=260, height=260,
            bg="#1a1a2e", highlightthickness=0,
        )
        self.canvas.pack(pady=(10, 0))

        cx = cy = 130
        self.canvas.create_arc(
            10, 10, 250, 250,
            start=90, extent=360,
            outline="#2a2a4a", width=6, style="arc",
        )
        self.arc = self.canvas.create_arc(
            10, 10, 250, 250,
            start=90, extent=360,
            outline=COLORS[self.mode], width=6, style="arc",
        )
        self.time_text = self.canvas.create_text(
            cx, cy - 8, text="25:00", fill="#eee",
            font=time_font, anchor="center",
        )
        self.phase_text = self.canvas.create_text(
            cx, cy + 38, text="专注时间", fill="#888",
            font=label_font, anchor="center",
        )

        # ── controls ──
        ctrl_frame = tk.Frame(self.root, bg="#1a1a2e")
        ctrl_frame.pack(pady=(16, 0))

        self.main_btn = tk.Button(
            ctrl_frame, text="开始", font=btn_font,
            bg=COLORS[self.mode], fg="#fff",
            width=10, relief="flat", cursor="hand2",
            activebackground="#ff5252", activeforeground="#fff",
            command=self._toggle,
        )
        self.main_btn.pack(side=tk.LEFT, padx=6)

        self.reset_btn = tk.Button(
            ctrl_frame, text="重置", font=btn_font,
            bg="#2a2a4a", fg="#ccc",
            width=8, relief="flat", cursor="hand2",
            activebackground="#3a3a5a", activeforeground="#fff",
            command=self._reset,
        )
        self.reset_btn.pack(side=tk.LEFT, padx=6)

        # ── stats ──
        self.stat_label = tk.Label(
            self.root,
            text=f"已完成 {self.completed} 个番茄",
            bg="#1a1a2e", fg="#666", font=stat_font,
        )
        self.stat_label.pack(pady=(16, 0))

        # ── notification ──
        self.notif_label = tk.Label(
            self.root, text="", bg="#1a1a2e", fg="#888", font=stat_font,
        )
        self.notif_label.pack(pady=(6, 0))

    # ── core logic ────────────────────────────────────────────────

    def _update_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.canvas.itemconfig(self.time_text, text=f"{mins:02d}:{secs:02d}")

        total = DURATIONS[self.mode] * 60
        fraction = self.time_left / total if total else 0
        self.canvas.itemconfig(self.arc, extent=360 * fraction)

    def _switch_mode(self, new_mode):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        if self.mode == new_mode:
            return

        self.mode = new_mode
        self.time_left = DURATIONS[self.mode] * 60

        for key, btn in self.tabs.items():
            active = key == new_mode
            btn.configure(
                bg="#2a2a4a" if active else "#1a1a2e",
                fg="#eee" if active else "#666",
            )
        self.canvas.itemconfig(self.arc, outline=COLORS[self.mode])
        self.main_btn.configure(bg=COLORS[self.mode], text="开始")
        self.canvas.itemconfig(self.phase_text, text=LABELS[self.mode])
        self._update_display()
        self.notif_label.config(text="")

    def _tick(self):
        self.time_left -= 1
        self._update_display()

        if self.time_left <= 0:
            self.timer_id = None
            self.main_btn.config(text="开始")

            if self.mode == "pomodoro":
                self.completed += 1
                self.session_count += 1
                self._save_count()
                self.stat_label.config(text=f"已完成 {self.completed} 个番茄")

                next_mode = "long_break" if self.session_count % 4 == 0 else "short_break"
                self._flash_notif(f"番茄完成! 开始{LABELS[next_mode]}吧")
                self._switch_mode(next_mode)
            else:
                self._flash_notif("休息结束，开始下一个番茄!")
                self._switch_mode("pomodoro")
        else:
            self.timer_id = self.root.after(1000, self._tick)

    def _toggle(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            self.main_btn.config(text="继续")
        else:
            self.timer_id = self.root.after(1000, self._tick)
            self.main_btn.config(text="暂停")

    def _reset(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.time_left = DURATIONS[self.mode] * 60
        self.main_btn.config(text="开始")
        self._update_display()
        self.notif_label.config(text="")

    def _flash_notif(self, msg):
        self.notif_label.config(text=msg)
        self.root.after(4000, lambda: self.notif_label.config(text=""))


if __name__ == "__main__":
    PomodoroTimer()
