from pynput import keyboard, mouse


def serialize_key(key) -> str:
    try:
        return key.char
    except AttributeError:
        return str(key)


def deserialize_key(value):
    if not isinstance(value, str):
        return None
    if value.startswith("Key."):
        name = value.split(".", 1)[1]
        return getattr(keyboard.Key, name, None)
    return value


def serialize_button(button) -> str:
    return str(button)


def deserialize_button(value):
    if not isinstance(value, str):
        return None
    if value.startswith("Button."):
        name = value.split(".", 1)[1]
        return getattr(mouse.Button, name, None)
    return None
