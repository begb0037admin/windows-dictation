"""
Step 4 of the MVP: paste cleaned-up text at the cursor via clipboard + a
simulated paste keystroke. Cross-platform: Ctrl+V on Windows, Cmd+V on Mac.

Clipboard-paste is used instead of simulating individual keystrokes because
Teams (and similar Electron/web-based apps) can drop characters or trigger
odd autocomplete behaviour with simulated typing — paste is far more
reliable. See docs/BUILD_BRIEF.md section 6.
"""

import platform
import time

import pyautogui
import pyperclip


def inject(text: str) -> None:
    """Copy text to the clipboard and simulate a paste at the cursor."""
    if not text.strip():
        return

    previous_clipboard = pyperclip.paste()
    pyperclip.copy(text)
    # Give the OS clipboard a moment to register the new content before the
    # paste keystroke fires — without this, fast key-up-to-paste sequences
    # can occasionally paste the previous clipboard contents instead.
    time.sleep(0.05)

    if platform.system() == "Darwin":
        pyautogui.hotkey("command", "v")
    else:
        pyautogui.hotkey("ctrl", "v")

    time.sleep(0.05)
    pyperclip.copy(previous_clipboard)
