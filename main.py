import threading
import sys
import ctypes
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

import customtkinter as ctk

from constants import (
    APP_TITLE,
    STATUS_READY,
    STATUS_RECORDING,
    STATUS_PLAYING,
    KILL_SWITCH_TEXT,
    DEFAULT_REPEAT,
    DEFAULT_LOOP_SECONDS,
)
from recorder import Recorder
from player import Player
from storage import save_macro, load_macro


class MacroApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("520x380")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#0E1116")

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
        container = ctk.CTkFrame(
            self.root,
            fg_color="#151A21",
            corner_radius=18,
        )
        container.pack(fill="both", expand=True, padx=12, pady=12)

        self.status_var = tk.StringVar(value=STATUS_READY)
        status_label = ctk.CTkLabel(
            container,
            textvariable=self.status_var,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="normal"),
            text_color="#E8EAED",
        )
        status_label.pack(pady=(6, 6))

        self.event_count_var = tk.StringVar(value="Events: 0")
        event_label = ctk.CTkLabel(
            container,
            textvariable=self.event_count_var,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#9AA4AF",
        )
        event_label.pack(pady=(0, 10))

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(pady=(0, 10))

        btn_font = ctk.CTkFont(family="Segoe UI", size=11)
        btn_style = {
            "fg_color": "#2A3038",
            "hover_color": "#343B45",
            "text_color": "#E8EAED",
            "corner_radius": 10,
            "width": 92,
            "height": 30,
            "font": btn_font,
        }
        self.record_btn = ctk.CTkButton(
            button_frame,
            text="Record",
            command=self.start_recording,
            **btn_style,
        )
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_action,
            **btn_style,
        )
        self.play_btn = ctk.CTkButton(
            button_frame,
            text="Play",
            command=self.play_macro,
            **btn_style,
        )
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_macro_dialog,
            **btn_style,
        )
        self.load_btn = ctk.CTkButton(
            button_frame,
            text="Load",
            command=self.load_macro_dialog,
            **btn_style,
        )

        self.record_btn.grid(row=0, column=0, padx=5, pady=4)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=4)
        self.play_btn.grid(row=0, column=2, padx=5, pady=4)
        self.save_btn.grid(row=1, column=0, padx=5, pady=4)
        self.load_btn.grid(row=1, column=1, padx=5, pady=4)

        options_card = ctk.CTkFrame(
            container,
            fg_color="#1A2028",
            corner_radius=14,
        )
        options_card.pack(fill="x", padx=12, pady=(0, 10))

        options_title = ctk.CTkLabel(
            options_card,
            text="Playback",
            text_color="#C7D0D9",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        options_title.pack(anchor="w", pady=(6, 4), padx=8)

        options_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        options_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.play_mode = tk.StringVar(value="once")
        radio_style = {
            "text_color": "#E8EAED",
            "fg_color": "#4C7AF2",
            "hover_color": "#5A86F5",
            "font": ctk.CTkFont(family="Segoe UI", size=10),
        }
        ctk.CTkRadioButton(
            options_frame,
            text="Play once",
            value="once",
            variable=self.play_mode,
            **radio_style,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkRadioButton(
            options_frame,
            text="Repeat N times",
            value="repeat",
            variable=self.play_mode,
            **radio_style,
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkRadioButton(
            options_frame,
            text="Loop for duration (seconds)",
            value="loop",
            variable=self.play_mode,
            **radio_style,
        ).grid(row=2, column=0, sticky="w")

        self.repeat_var = tk.StringVar(value=str(DEFAULT_REPEAT))
        repeat_entry = ctk.CTkEntry(
            options_frame,
            textvariable=self.repeat_var,
            width=64,
            height=26,
            corner_radius=8,
            fg_color="#242B33",
            text_color="#E8EAED",
            border_color="#2F3742",
            border_width=1,
        )
        repeat_entry.grid(row=1, column=1, padx=(10, 0), sticky="w")

        self.loop_var = tk.StringVar(value=str(DEFAULT_LOOP_SECONDS))
        loop_entry = ctk.CTkEntry(
            options_frame,
            textvariable=self.loop_var,
            width=64,
            height=26,
            corner_radius=8,
            fg_color="#242B33",
            text_color="#E8EAED",
            border_color="#2F3742",
            border_width=1,
        )
        loop_entry.grid(row=2, column=1, padx=(10, 0), sticky="w")

        kill_label = ctk.CTkLabel(
            container,
            text=KILL_SWITCH_TEXT,
            text_color="#9AA4AF",
            font=ctk.CTkFont(family="Segoe UI", size=9),
        )
        kill_label.pack(pady=(0, 6))

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _update_event_count(self) -> None:
        self.event_count_var.set(f"Events: {len(self.events)}")

    def _update_controls(self) -> None:
        is_recording = self.recorder.is_recording
        is_playing = self.player.is_playing
        has_events = bool(self.events)

        self.record_btn.configure(state="disabled" if is_recording or is_playing else "normal")
        self.stop_btn.configure(state="normal" if is_recording or is_playing else "disabled")
        self.play_btn.configure(
            state="normal" if (has_events and not is_recording and not is_playing) else "disabled"
        )
        self.save_btn.configure(
            state="normal" if (has_events and not is_recording and not is_playing) else "disabled"
        )
        self.load_btn.configure(state="normal" if not (is_recording or is_playing) else "disabled")

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
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    app = MacroApp(root)
    root.mainloop()
