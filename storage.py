import json
from datetime import datetime
from pathlib import Path


def save_macro(events, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "created": datetime.now().isoformat(timespec="seconds"),
        "events": list(events),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def load_macro(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    events = _validate_events(payload.get("events", []))
    return events


def _validate_events(raw_events):
    if not isinstance(raw_events, list):
        return []
    cleaned = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            continue
        event_type = raw.get("type")
        if event_type == "mouse_click":
            event = _validate_mouse_click(raw)
        elif event_type == "mouse_scroll":
            event = _validate_mouse_scroll(raw)
        elif event_type == "key":
            event = _validate_key(raw)
        else:
            event = None
        if event is not None:
            cleaned.append(event)
    cleaned.sort(key=lambda item: item["t"])
    return cleaned


def _coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _validate_base(raw):
    t_value = _coerce_float(raw.get("t"))
    if t_value is None or t_value < 0:
        return None
    return t_value


def _validate_mouse_click(raw):
    t_value = _validate_base(raw)
    if t_value is None:
        return None
    x_value = _coerce_int(raw.get("x"))
    y_value = _coerce_int(raw.get("y"))
    button = raw.get("button")
    pressed = raw.get("pressed")
    if x_value is None or y_value is None or not isinstance(button, str):
        return None
    if isinstance(pressed, bool):
        pressed_value = pressed
    elif pressed in (0, 1):
        pressed_value = bool(pressed)
    else:
        return None
    return {
        "t": t_value,
        "type": "mouse_click",
        "x": x_value,
        "y": y_value,
        "button": button,
        "pressed": pressed_value,
    }


def _validate_mouse_scroll(raw):
    t_value = _validate_base(raw)
    if t_value is None:
        return None
    x_value = _coerce_int(raw.get("x"))
    y_value = _coerce_int(raw.get("y"))
    dx_value = _coerce_int(raw.get("dx"))
    dy_value = _coerce_int(raw.get("dy"))
    if None in (x_value, y_value, dx_value, dy_value):
        return None
    return {
        "t": t_value,
        "type": "mouse_scroll",
        "x": x_value,
        "y": y_value,
        "dx": dx_value,
        "dy": dy_value,
    }


def _validate_key(raw):
    t_value = _validate_base(raw)
    if t_value is None:
        return None
    key_value = raw.get("key")
    action = raw.get("action")
    if not isinstance(key_value, str):
        return None
    if action not in ("press", "release"):
        return None
    return {
        "t": t_value,
        "type": "key",
        "action": action,
        "key": key_value,
    }
