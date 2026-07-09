"""
Step 1 of the MVP: push-to-talk hotkey + audio capture to memory + tray icon.
Cross-platform (Windows + macOS) via pynput and sounddevice.

No transcription, cleanup, or text injection yet — those are later steps.
Run this, hold the hotkey (Right Ctrl on Windows, Right Option on Mac by
default), speak, release, and check the console for a line reporting how
many samples/seconds were captured. Confirm that works before Step 2
(transcription) is wired up.

macOS note: the hotkey listener needs Accessibility permission granted to
whatever runs this script (Terminal, or your Python interpreter) under
System Settings > Privacy & Security > Accessibility. Without it, pynput
silently receives no key events at all.
"""

import platform
import sys
import threading

import numpy as np
import sounddevice as sd
from pynput import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

from config import load_config

config = load_config()
SAMPLE_RATE = config["sample_rate"]
HOTKEY_NAME = config["hotkey"]


def resolve_hotkey(name):
    key = getattr(keyboard.Key, name, None)
    if key is not None:
        return key
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    raise ValueError(
        f"Unrecognised hotkey '{name}' — use a pynput Key name "
        f"(e.g. 'ctrl_r', 'alt_r', 'cmd_r') or a single character"
    )


HOTKEY = resolve_hotkey(HOTKEY_NAME)

state_lock = threading.Lock()
recording = False
frames = []
stream = None
tray_icon = None


def make_icon_image(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img


ICON_IDLE = make_icon_image((90, 90, 90, 255))
ICON_RECORDING = make_icon_image((220, 40, 40, 255))


def audio_callback(indata, frame_count, time_info, status):
    if status:
        print(f"[audio] status: {status}", file=sys.stderr)
    with state_lock:
        if recording:
            frames.append(indata.copy())


def start_recording():
    global recording, frames, stream
    with state_lock:
        if recording:
            return
        recording = True
        frames = []
    if tray_icon:
        tray_icon.icon = ICON_RECORDING
    print("[rec] recording started")
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    )
    stream.start()


def stop_recording():
    global recording, stream
    with state_lock:
        if not recording:
            return
        recording = False
    if stream:
        stream.stop()
        stream.close()
        stream = None
    if tray_icon:
        tray_icon.icon = ICON_IDLE

    with state_lock:
        captured = list(frames)

    if not captured:
        print("[rec] recording stopped — no audio captured")
        return

    audio = np.concatenate(captured, axis=0)
    duration_s = len(audio) / SAMPLE_RATE
    print(
        f"[rec] recording stopped — {len(audio)} samples, "
        f"{duration_s:.2f}s captured at {SAMPLE_RATE}Hz"
    )


def on_press(key):
    print(f"[debug] key pressed: {key!r} (looking for {HOTKEY!r})")
    if key == HOTKEY:
        start_recording()


def on_release(key):
    if key == HOTKEY:
        stop_recording()


def run_hotkey_listener():
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener


def quit_app(icon, item):
    icon.stop()


def run_tray():
    global tray_icon
    tray_icon = Icon(
        "windows-dictation",
        ICON_IDLE,
        "Dictation (idle)",
        menu=Menu(MenuItem("Quit", quit_app)),
    )
    tray_icon.run()


def main():
    try:
        sd.check_input_settings(samplerate=SAMPLE_RATE, channels=1)
    except Exception as exc:
        print(f"[mic] no usable microphone found: {exc}", file=sys.stderr)
        if platform.system() == "Darwin":
            print(
                "[mic] grant microphone access: System Settings > Privacy & "
                "Security > Microphone > enable for Terminal (or your Python "
                "interpreter).",
                file=sys.stderr,
            )
        else:
            print(
                "[mic] check Windows microphone permissions for this app "
                "(Settings > Privacy & security > Microphone).",
                file=sys.stderr,
            )
        sys.exit(1)

    print(
        f"[main] windows-dictation starting on {platform.system()} — "
        f"hold '{HOTKEY_NAME}' to record"
    )
    if platform.system() == "Darwin":
        print(
            "[main] macOS: this needs Accessibility permission granted to "
            "Terminal / your Python interpreter under System Settings > "
            "Privacy & Security > Accessibility, or the hotkey listener will "
            "silently receive no events."
        )

    run_hotkey_listener()
    run_tray()


if __name__ == "__main__":
    main()
