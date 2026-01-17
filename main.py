import threading
import tkinter as tk
import sys
import ctypes
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
        self.root.configure(bg="#0E1116")

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
        container_canvas, container = self._create_card(
            self.root,
            width=496,
            height=356,
            radius=18,
            card_bg="#151A21",
            canvas_bg="#0E1116",
        )
        container_canvas.pack(padx=12, pady=12)

        self.status_var = tk.StringVar(value=STATUS_READY)
        status_label = tk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 16),
            fg="#E8EAED",
            bg="#151A21",
        )
        status_label.pack(pady=(0, 8))

        self.event_count_var = tk.StringVar(value="Events: 0")
        event_label = tk.Label(
            container,
            textvariable=self.event_count_var,
            font=("Segoe UI", 10),
            fg="#9AA4AF",
            bg="#151A21",
        )
        event_label.pack(pady=(0, 8))

        button_frame = tk.Frame(container, bg="#151A21")
        button_frame.pack(pady=(0, 10))

        btn_font = ("Segoe UI", 11)
        btn_style = {
            "bg": "#2A3038",
            "fg": "#E8EAED",
            "activebackground": "#343B45",
            "activeforeground": "#FFFFFF",
            "font": btn_font,
            "radius": 10,
            "width": 92,
            "height": 30,
        }
        self.record_btn = RoundedButton(
            button_frame,
            text="Record",
            command=self.start_recording,
            **btn_style,
        )
        self.stop_btn = RoundedButton(
            button_frame,
            text="Stop",
            command=self.stop_action,
            **btn_style,
        )
        self.play_btn = RoundedButton(
            button_frame,
            text="Play",
            command=self.play_macro,
            **btn_style,
        )
        self.save_btn = RoundedButton(
            button_frame,
            text="Save",
            command=self.save_macro_dialog,
            **btn_style,
        )
        self.load_btn = RoundedButton(
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

        options_canvas, options_card = self._create_card(
            container,
            width=456,
            height=118,
            radius=14,
            card_bg="#1A2028",
            canvas_bg="#151A21",
        )
        options_canvas.pack(pady=(0, 10))

        options_title = tk.Label(
            options_card,
            text="Playback",
            fg="#C7D0D9",
            bg="#1A2028",
            font=("Segoe UI", 10),
        )
        options_title.pack(anchor="w", pady=(2, 6), padx=6)

        options_frame = tk.Frame(options_card, bg="#1A2028")
        options_frame.pack(fill="x", padx=4)

        self.play_mode = tk.StringVar(value="once")
        tk.Radiobutton(
            options_frame,
            text="Play once",
            value="once",
            variable=self.play_mode,
            bg="#1A2028",
            fg="#E8EAED",
            activebackground="#1A2028",
            activeforeground="#FFFFFF",
            selectcolor="#2A3038",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(
            options_frame,
            text="Repeat N times",
            value="repeat",
            variable=self.play_mode,
            bg="#1A2028",
            fg="#E8EAED",
            activebackground="#1A2028",
            activeforeground="#FFFFFF",
            selectcolor="#2A3038",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(
            options_frame,
            text="Loop for duration (seconds)",
            value="loop",
            variable=self.play_mode,
            bg="#1A2028",
            fg="#E8EAED",
            activebackground="#1A2028",
            activeforeground="#FFFFFF",
            selectcolor="#2A3038",
            font=("Segoe UI", 10),
        ).grid(row=2, column=0, sticky="w")

        self.repeat_var = tk.StringVar(value=str(DEFAULT_REPEAT))
        repeat_entry = tk.Entry(
            options_frame,
            textvariable=self.repeat_var,
            width=6,
            bg="#242B33",
            fg="#E8EAED",
            insertbackground="#E8EAED",
            relief="flat",
        )
        repeat_entry.grid(row=1, column=1, padx=(10, 0), sticky="w")

        self.loop_var = tk.StringVar(value=str(DEFAULT_LOOP_SECONDS))
        loop_entry = tk.Entry(
            options_frame,
            textvariable=self.loop_var,
            width=6,
            bg="#242B33",
            fg="#E8EAED",
            insertbackground="#E8EAED",
            relief="flat",
        )
        loop_entry.grid(row=2, column=1, padx=(10, 0), sticky="w")

        warning_label = tk.Label(
            container,
            text=WARNING_TEXT,
            fg="#F3A8A0",
            bg="#151A21",
            font=("Segoe UI", 9),
            wraplength=460,
            justify="center",
        )
        warning_label.pack(pady=(0, 4))

        kill_label = tk.Label(
            container,
            text=KILL_SWITCH_TEXT,
            font=("Segoe UI", 9),
            fg="#9AA4AF",
            bg="#151A21",
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

    def _create_card(self, parent, width, height, radius, card_bg, canvas_bg):
        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self._draw_rounded_rect(canvas, 0, 0, width, height, radius, card_bg)
        frame = tk.Frame(canvas, bg=card_bg)
        canvas.create_window((width // 2, height // 2), window=frame, width=width - 18, height=height - 18)
        return canvas, frame

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        canvas.create_polygon(points, smooth=True, fill=fill, outline=fill)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width, height, radius, bg, fg, activebackground, activeforeground, font):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, bd=0)
        self._bg = bg
        self._fg = fg
        self._active_bg = activebackground
        self._active_fg = activeforeground
        self._command = command
        self._radius = radius
        self._width = width
        self._height = height
        self._enabled = True
        self._rect = self._draw(radius, bg)
        self._label = self.create_text(width // 2, height // 2, text=text, fill=fg, font=font)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_release)

    def config(self, **kwargs):
        if "state" in kwargs:
            state = kwargs["state"]
            if state == "disabled":
                self._enabled = False
                self.itemconfigure(self._rect, fill="#1F252C", outline="#1F252C")
                self.itemconfigure(self._label, fill="#6C747D")
                self.unbind("<Button-1>")
            else:
                self._enabled = True
                self.itemconfigure(self._rect, fill=self._bg, outline=self._bg)
                self.itemconfigure(self._label, fill=self._fg)
                self.bind("<Button-1>", self._on_click)

    def _draw(self, radius, fill):
        points = [
            radius, 0,
            self._width - radius, 0,
            self._width, 0,
            self._width, radius,
            self._width, self._height - radius,
            self._width, self._height,
            self._width - radius, self._height,
            radius, self._height,
            0, self._height,
            0, self._height - radius,
            0, radius,
            0, 0,
        ]
        return self.create_polygon(points, smooth=True, fill=fill, outline=fill)

    def _on_click(self, _event):
        if not self._enabled:
            return
        if callable(self._command):
            self._command()

    def _on_enter(self, _event):
        if not self._enabled:
            return
        self.itemconfigure(self._rect, fill=self._active_bg, outline=self._active_bg)
        self.itemconfigure(self._label, fill=self._active_fg)

    def _on_leave(self, _event):
        if not self._enabled:
            return
        self.itemconfigure(self._rect, fill=self._bg, outline=self._bg)
        self.itemconfigure(self._label, fill=self._fg)

    def _on_release(self, _event):
        self._on_enter(_event)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()
