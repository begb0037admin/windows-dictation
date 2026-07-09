"""
Step 1 of the MVP: push-to-talk hotkey + audio capture to memory + tray icon.

No transcription, cleanup, or text injection yet — those are later steps.
Run this, hold the hotkey (default: Caps Lock), speak, release, and check
the console for a line reporting how many samples/seconds were captured.
Confirm that works before Step 2 (transcription) is wired up.
"""

import sys
import threading

import numpy as np
import sounddevice as sd
import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

from config import load_config

config = load_config()
SAMPLE_RATE = config["sample_rate"]
HOTKEY = config["hotkey"]

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


def register_hotkey():
    try:
        keyboard.on_press_key(HOTKEY, lambda e: start_recording(), suppress=True)
        keyboard.on_release_key(HOTKEY, lambda e: stop_recording(), suppress=True)
    except Exception as exc:
        print(f"[hotkey] failed to register '{HOTKEY}': {exc}", file=sys.stderr)
        print(
            "[hotkey] this usually means the process needs to run as "
            "Administrator to hook a global hotkey on Windows.",
            file=sys.stderr,
        )
        sys.exit(1)


def quit_app(icon, item):
    icon.stop()


def run_tray():
    global tray_icon
    tray_icon = Icon(
        "windows-dictation",
        ICON_IDLE,
        "Windows Dictation (idle)",
        menu=Menu(MenuItem("Quit", quit_app)),
    )
    tray_icon.run()


def main():
    try:
        sd.check_input_settings(samplerate=SAMPLE_RATE, channels=1)
    except Exception as exc:
        print(f"[mic] no usable microphone found: {exc}", file=sys.stderr)
        print(
            "[mic] check Windows microphone permissions for this app "
            "(Settings > Privacy & security > Microphone).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[main] windows-dictation starting — hold '{HOTKEY}' to record")
    register_hotkey()
    run_tray()


if __name__ == "__main__":
    main()
