import time
import threading
from pynput import mouse, keyboard

from models import deserialize_button, deserialize_key


class Player:
    def __init__(self) -> None:
        self.is_playing = False
        self._stop_event = threading.Event()
        self._esc_listener = None
        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()

    def stop(self) -> None:
        self._stop_event.set()

    def play(self, events, mode="once", repeat_count=1, loop_seconds=0):
        if self.is_playing:
            return
        self.is_playing = True
        self._stop_event.clear()
        self._start_kill_switch()
        try:
            if mode == "repeat":
                for _ in range(max(1, repeat_count)):
                    if self._stop_event.is_set():
                        break
                    self._play_sequence(events)
            elif mode == "loop":
                end_time = time.monotonic() + max(0.0, loop_seconds)
                while time.monotonic() < end_time:
                    if self._stop_event.is_set():
                        break
                    self._play_sequence(events)
            else:
                self._play_sequence(events)
        finally:
            self.is_playing = False
            self._stop_event.set()
            self._stop_kill_switch()

    def _start_kill_switch(self) -> None:
        def on_press(key):
            if key == keyboard.Key.esc:
                self._stop_event.set()
                return False
            return True

        self._esc_listener = keyboard.Listener(on_press=on_press)
        self._esc_listener.start()

    def _stop_kill_switch(self) -> None:
        if self._esc_listener is not None:
            self._esc_listener.stop()
            self._esc_listener = None

    def _play_sequence(self, events) -> None:
        if not events:
            return
        start_time = time.monotonic()
        for event in events:
            if self._stop_event.is_set():
                break
            target_time = start_time + float(event.get("t", 0.0))
            self._sleep_until(target_time)
            if self._stop_event.is_set():
                break
            self._dispatch_event(event)

    def _sleep_until(self, target_time: float) -> None:
        while True:
            if self._stop_event.is_set():
                return
            remaining = target_time - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(remaining, 0.01))

    def _dispatch_event(self, event: dict) -> None:
        event_type = event.get("type")
        if event_type == "mouse_click":
            button = deserialize_button(event.get("button"))
            if button is None:
                return
            self._mouse.position = (event.get("x", 0), event.get("y", 0))
            if event.get("pressed"):
                self._mouse.press(button)
            else:
                self._mouse.release(button)
        elif event_type == "mouse_scroll":
            self._mouse.position = (event.get("x", 0), event.get("y", 0))
            self._mouse.scroll(event.get("dx", 0), event.get("dy", 0))
        elif event_type == "key":
            key_value = deserialize_key(event.get("key"))
            if key_value is None:
                return
            action = event.get("action")
            if action == "press":
                self._keyboard.press(key_value)
            elif action == "release":
                self._keyboard.release(key_value)
