import time
import threading
from pynput import mouse, keyboard

from constants import MOVE_MIN_DISTANCE, MOVE_MIN_INTERVAL
from models import serialize_button, serialize_key


class Recorder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_time = None
        self._mouse_listener = None
        self._keyboard_listener = None
        self._events = []
        self._last_move_time = None
        self._last_move_pos = None
        self.is_recording = False

    def start(self) -> None:
        if self.is_recording:
            return
        self._events = []
        self._start_time = time.monotonic()
        self._last_move_time = None
        self._last_move_pos = None
        self.is_recording = True

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> None:
        if not self.is_recording:
            return
        self.is_recording = False
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()

    def get_events(self):
        with self._lock:
            return sorted(self._events, key=lambda item: item.get("t", 0.0))

    def _timestamp(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time

    def _append_event(self, event: dict) -> None:
        with self._lock:
            self._events.append(event)

    def _on_click(self, x, y, button, pressed):
        event = {
            "t": self._timestamp(),
            "type": "mouse_click",
            "x": int(x),
            "y": int(y),
            "button": serialize_button(button),
            "pressed": bool(pressed),
        }
        self._append_event(event)

    def _on_move(self, x, y):
        timestamp = self._timestamp()
        if self._last_move_time is not None:
            elapsed = timestamp - self._last_move_time
            last_x, last_y = self._last_move_pos
            distance = abs(int(x) - last_x) + abs(int(y) - last_y)
            if elapsed < MOVE_MIN_INTERVAL and distance < MOVE_MIN_DISTANCE:
                return
        self._last_move_time = timestamp
        self._last_move_pos = (int(x), int(y))
        event = {
            "t": timestamp,
            "type": "mouse_move",
            "x": int(x),
            "y": int(y),
        }
        self._append_event(event)

    def _on_scroll(self, x, y, dx, dy):
        event = {
            "t": self._timestamp(),
            "type": "mouse_scroll",
            "x": int(x),
            "y": int(y),
            "dx": int(dx),
            "dy": int(dy),
        }
        self._append_event(event)

    def _on_press(self, key):
        event = {
            "t": self._timestamp(),
            "type": "key",
            "action": "press",
            "key": serialize_key(key),
        }
        self._append_event(event)

    def _on_release(self, key):
        event = {
            "t": self._timestamp(),
            "type": "key",
            "action": "release",
            "key": serialize_key(key),
        }
        self._append_event(event)
