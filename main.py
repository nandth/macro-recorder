import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from constants import (
    APP_TITLE,
    STATUS_READY,
    STATUS_RECORDING,
    STATUS_PLAYING,
    WARNING_TEXT,
    KILL_SWITCH_TEXT,
    DEFAULT_REPEAT,
    DEFAULT_LOOP_SECONDS,
)
from recorder import Recorder
from player import Player
from storage import save_macro, load_macro


class MacroApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("520x380")
        self.root.resizable(False, False)
        self.root.configure(bg="#101214")

        self.recorder = Recorder()
        self.player = Player()
        self.events = []

        self.macros_dir = Path(__file__).resolve().parent / "macros"
        self.macros_dir.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._set_status(STATUS_READY)
        self._update_event_count()
        self._update_controls()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, padx=12, pady=10, bg="#101214")
        container.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value=STATUS_READY)
        status_label = tk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 16, "bold"),
            fg="#E6E6E6",
            bg="#101214",
        )
        status_label.pack(pady=(0, 8))

        self.event_count_var = tk.StringVar(value="Events: 0")
        event_label = tk.Label(
            container,
            textvariable=self.event_count_var,
            font=("Segoe UI", 10),
            fg="#B9C0C7",
            bg="#101214",
        )
        event_label.pack(pady=(0, 8))

        button_frame = tk.Frame(container, bg="#101214")
        button_frame.pack(pady=(0, 10))

        btn_font = ("Segoe UI", 11, "bold")
        btn_style = {
            "bg": "#1F2328",
            "fg": "#E6E6E6",
            "activebackground": "#2B3036",
            "activeforeground": "#FFFFFF",
            "relief": "flat",
            "bd": 0,
            "highlightthickness": 0,
        }
        self.record_btn = tk.Button(
            button_frame,
            text="Record",
            width=9,
            height=1,
            font=btn_font,
            command=self.start_recording,
            **btn_style,
        )
        self.stop_btn = tk.Button(
            button_frame,
            text="Stop",
            width=9,
            height=1,
            font=btn_font,
            command=self.stop_action,
            **btn_style,
        )
        self.play_btn = tk.Button(
            button_frame,
            text="Play",
            width=9,
            height=1,
            font=btn_font,
            command=self.play_macro,
            **btn_style,
        )
        self.save_btn = tk.Button(
            button_frame,
            text="Save",
            width=9,
            height=1,
            font=btn_font,
            command=self.save_macro_dialog,
            **btn_style,
        )
        self.load_btn = tk.Button(
            button_frame,
            text="Load",
            width=9,
            height=1,
            font=btn_font,
            command=self.load_macro_dialog,
            **btn_style,
        )

        self.record_btn.grid(row=0, column=0, padx=5, pady=4)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=4)
        self.play_btn.grid(row=0, column=2, padx=5, pady=4)
        self.save_btn.grid(row=1, column=0, padx=5, pady=4)
        self.load_btn.grid(row=1, column=1, padx=5, pady=4)

        options_frame = tk.LabelFrame(
            container,
            text="Playback",
            padx=10,
            pady=6,
            bg="#101214",
            fg="#B9C0C7",
            font=("Segoe UI", 10, "bold"),
            labelanchor="n",
        )
        options_frame.pack(fill="x", pady=(0, 10))

        self.play_mode = tk.StringVar(value="once")
        tk.Radiobutton(
            options_frame,
            text="Play once",
            value="once",
            variable=self.play_mode,
            bg="#101214",
            fg="#E6E6E6",
            activebackground="#101214",
            activeforeground="#FFFFFF",
            selectcolor="#1F2328",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(
            options_frame,
            text="Repeat N times",
            value="repeat",
            variable=self.play_mode,
            bg="#101214",
            fg="#E6E6E6",
            activebackground="#101214",
            activeforeground="#FFFFFF",
            selectcolor="#1F2328",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(
            options_frame,
            text="Loop for duration (seconds)",
            value="loop",
            variable=self.play_mode,
            bg="#101214",
            fg="#E6E6E6",
            activebackground="#101214",
            activeforeground="#FFFFFF",
            selectcolor="#1F2328",
            font=("Segoe UI", 10),
        ).grid(row=2, column=0, sticky="w")

        self.repeat_var = tk.StringVar(value=str(DEFAULT_REPEAT))
        repeat_entry = tk.Entry(
            options_frame,
            textvariable=self.repeat_var,
            width=6,
            bg="#1F2328",
            fg="#E6E6E6",
            insertbackground="#E6E6E6",
            relief="flat",
        )
        repeat_entry.grid(row=1, column=1, padx=(10, 0), sticky="w")

        self.loop_var = tk.StringVar(value=str(DEFAULT_LOOP_SECONDS))
        loop_entry = tk.Entry(
            options_frame,
            textvariable=self.loop_var,
            width=6,
            bg="#1F2328",
            fg="#E6E6E6",
            insertbackground="#E6E6E6",
            relief="flat",
        )
        loop_entry.grid(row=2, column=1, padx=(10, 0), sticky="w")

        warning_label = tk.Label(
            container,
            text=WARNING_TEXT,
            fg="#FF7B72",
            bg="#101214",
            font=("Segoe UI", 9, "bold"),
            wraplength=460,
            justify="center",
        )
        warning_label.pack(pady=(0, 4))

        kill_label = tk.Label(
            container,
            text=KILL_SWITCH_TEXT,
            font=("Segoe UI", 9),
            fg="#B9C0C7",
            bg="#101214",
        )
        kill_label.pack(pady=(0, 4))

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _update_event_count(self) -> None:
        self.event_count_var.set(f"Events: {len(self.events)}")

    def _update_controls(self) -> None:
        is_recording = self.recorder.is_recording
        is_playing = self.player.is_playing
        has_events = bool(self.events)

        self.record_btn.config(state="disabled" if is_recording or is_playing else "normal")
        self.stop_btn.config(state="normal" if is_recording or is_playing else "disabled")
        self.play_btn.config(
            state="normal" if (has_events and not is_recording and not is_playing) else "disabled"
        )
        self.save_btn.config(
            state="normal" if (has_events and not is_recording and not is_playing) else "disabled"
        )
        self.load_btn.config(state="normal" if not (is_recording or is_playing) else "disabled")

    def start_recording(self) -> None:
        if self.player.is_playing:
            return
        self.events = []
        self._update_event_count()
        self.recorder.start()
        self._set_status(STATUS_RECORDING)
        self._update_controls()

    def stop_action(self) -> None:
        if self.recorder.is_recording:
            self.recorder.stop()
            self.events = self.recorder.get_events()
            self._set_status(STATUS_READY)
        elif self.player.is_playing:
            self.player.stop()
            self._set_status(STATUS_READY)
        self._update_event_count()
        self._update_controls()

    def play_macro(self) -> None:
        if self.recorder.is_recording or self.player.is_playing:
            return
        if not self.events:
            messagebox.showinfo(APP_TITLE, "No events to play yet.")
            return

        mode = self.play_mode.get()
        repeat_count = self._parse_int(self.repeat_var.get(), DEFAULT_REPEAT)
        loop_seconds = self._parse_float(self.loop_var.get(), DEFAULT_LOOP_SECONDS)

        self._set_status(STATUS_PLAYING)
        self._update_controls()

        def runner():
            self.player.play(
                list(self.events),
                mode=mode,
                repeat_count=repeat_count,
                loop_seconds=loop_seconds,
            )
            self.root.after(0, self._on_playback_finished)

        threading.Thread(target=runner, daemon=True).start()

    def _on_playback_finished(self) -> None:
        self._set_status(STATUS_READY)
        self._update_controls()

    def _on_close(self) -> None:
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.player.is_playing:
            self.player.stop()
        self.root.destroy()

    def save_macro_dialog(self) -> None:
        if not self.events:
            messagebox.showinfo(APP_TITLE, "No recorded events to save.")
            return
        default_name = "macro.json"
        path = filedialog.asksaveasfilename(
            title="Save Macro",
            defaultextension=".json",
            filetypes=[("Macro JSON", "*.json")],
            initialdir=str(self.macros_dir),
            initialfile=default_name,
        )
        if not path:
            return
        save_macro(self.events, Path(path))

    def load_macro_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Macro",
            filetypes=[("Macro JSON", "*.json")],
            initialdir=str(self.macros_dir),
        )
        if not path:
            return
        events = load_macro(Path(path))
        if not events:
            messagebox.showwarning(APP_TITLE, "No valid events found in that file.")
        self.events = events
        self._update_event_count()
        self._update_controls()

    def _parse_int(self, value, default):
        try:
            parsed = int(value)
            return parsed if parsed > 0 else default
        except ValueError:
            return default

    def _parse_float(self, value, default):
        try:
            parsed = float(value)
            return parsed if parsed > 0 else default
        except ValueError:
            return default


if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()
