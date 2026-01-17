# Macro Maker (Local Only)

A lightweight desktop app for recording and replaying mouse and keyboard macros on your own machine.

## Features
- Record mouse movements, clicks, scrolls, and keyboard press/release events with precise timing.
- Play back once, repeat N times, or loop for a duration.
- Save/load readable JSON macros in the `macros/` folder.
- Clear status indicator and a hard kill switch (ESC) to abort playback.

## Requirements
- Python 3.9+
- `pynput`
- `customtkinter`

## Setup
1. Install dependencies:

```bash
pip install pynput customtkinter
```

2. Run the app:

```bash
python main.py
```

## Safety
- Do not record passwords or other sensitive input.
- Press ESC at any time during playback to stop immediately.
- Recording only starts when you click the Record button.

## Notes
- On some systems, global input capture may require accessibility permissions.
- This tool is local-only and does not send data anywhere.
