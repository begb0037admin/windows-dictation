"""
Full MVP pipeline: push-to-talk hotkey + audio capture + transcription +
Ollama cleanup + clipboard paste injection. Cross-platform (Windows + macOS)
via pynput, sounddevice, transcribe.py, cleanup.py, and inject.py.

This is a normal, always-visible app window (not a system tray utility).
The window shows live status and a live-updating partial transcript while
you hold the hotkey, purely for feedback that it's hearing you — the real
text only gets pasted into whatever app has focus once, cleanly, on
release. Closing the window quits the app.

Hold the hotkey (Right Ctrl on Windows, Right Option on Mac by default),
speak, release.

macOS note: the hotkey listener AND the paste injection need Accessibility
permission granted to whatever runs this script (Terminal, or your Python
interpreter) under System Settings > Privacy & Security > Accessibility.
Without it, pynput silently receives no key events, and pyautogui's paste
keystroke silently does nothing.
"""

import os
import platform
import sys
import threading
import tkinter as tk

import numpy as np
import sounddevice as sd
from pynput import keyboard

from cleanup import cleanup
from config import load_config
from inject import inject
from transcribe import transcribe

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
HOTKEY_DISPLAY = HOTKEY_NAME.replace("_r", " (right)").replace("_l", " (left)").replace("_", " ").title()
IDLE_STATUS = f"Idle — hold {HOTKEY_DISPLAY} to record"

state_lock = threading.Lock()
transcribe_lock = threading.Lock()
recording = False
frames = []
stream = None
partial_stop_event = None

root = None
status_label = None
text_box = None


def set_status(text):
    if root:
        root.after(0, lambda: status_label.config(text=text))


def set_text(text):
    if root:
        def _update():
            text_box.config(state="normal")
            text_box.delete("1.0", "end")
            text_box.insert("1.0", text)
            text_box.config(state="disabled")

        root.after(0, _update)


def audio_callback(indata, frame_count, time_info, status):
    if status:
        print(f"[audio] status: {status}", file=sys.stderr)
    with state_lock:
        if recording:
            frames.append(indata.copy())


PARTIAL_INTERVAL_SECONDS = 0.8
CHUNK_SECONDS = 5


def partial_transcription_loop(stop_event):
    """While recording, show a live-updating transcript that never loses
    earlier words: audio is split into ~5s chunks; once a chunk is that
    long it's "finalized" (transcribed once, appended permanently to
    finalized_text, never re-transcribed again) while the current
    in-progress chunk keeps re-transcribing every ~0.8s for the live feel.
    This keeps each call bounded to ~5s of audio — fast regardless of how
    long the whole recording runs — while still showing the full transcript
    built up so far. Pure visual feedback, never pasted; the final paste
    re-transcribes the complete recording in one shot after release for
    maximum accuracy."""
    finalized_text = ""
    chunk_start = 0

    while not stop_event.wait(PARTIAL_INTERVAL_SECONDS):
        with state_lock:
            if not recording:
                return
            snapshot = list(frames)
        if not snapshot:
            continue
        audio_so_far = np.concatenate(snapshot, axis=0)
        chunk_audio = audio_so_far[chunk_start:]
        if len(chunk_audio) < SAMPLE_RATE * 0.5:
            continue
        try:
            with transcribe_lock:
                partial_text = transcribe(chunk_audio, SAMPLE_RATE, config["whisper"])
        except Exception:
            continue

        display_text = f"{finalized_text} {partial_text}".strip()
        if display_text:
            set_text(display_text)

        if len(chunk_audio) >= CHUNK_SECONDS * SAMPLE_RATE:
            finalized_text = display_text
            chunk_start = len(audio_so_far)


def start_recording():
    global recording, frames, stream, partial_stop_event
    with state_lock:
        if recording:
            return
        recording = True
        frames = []
    set_status("Listening...")
    set_text("")
    print("[rec] recording started")
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    )
    stream.start()
    partial_stop_event = threading.Event()
    threading.Thread(
        target=partial_transcription_loop, args=(partial_stop_event,), daemon=True
    ).start()


def stop_recording():
    global recording, stream
    with state_lock:
        if not recording:
            return
        recording = False
    if partial_stop_event:
        partial_stop_event.set()
    if stream:
        stream.stop()
        stream.close()
        stream = None

    with state_lock:
        captured = list(frames)

    if not captured:
        print("[rec] recording stopped — no audio captured")
        set_status(IDLE_STATUS)
        return

    audio = np.concatenate(captured, axis=0)
    duration_s = len(audio) / SAMPLE_RATE
    print(
        f"[rec] recording stopped — {len(audio)} samples, "
        f"{duration_s:.2f}s captured at {SAMPLE_RATE}Hz"
    )

    set_status("Transcribing...")
    try:
        with transcribe_lock:
            text = transcribe(audio, SAMPLE_RATE, config["whisper"])
        print(f"[transcribe] result: {text!r}")
    except Exception as exc:
        print(f"[transcribe] failed: {exc}", file=sys.stderr)
        set_status(f"Transcription failed: {exc}")
        return

    set_text(text)
    set_status("Cleaning up...")
    try:
        cleaned = cleanup(text, config["cleanup"])
        print(f"[cleanup] result: {cleaned!r}")
    except Exception as exc:
        print(f"[cleanup] failed: {exc}", file=sys.stderr)
        print("[cleanup] falling back to the raw transcript for injection")
        cleaned = text

    set_text(cleaned)
    set_status("Pasting...")
    try:
        inject(cleaned)
        set_status(IDLE_STATUS)
    except Exception as exc:
        print(f"[inject] failed: {exc}", file=sys.stderr)
        set_status(f"Paste failed: {exc}")


def on_press(key):
    if key == HOTKEY:
        start_recording()


def on_release(key):
    if key == HOTKEY:
        stop_recording()


def run_hotkey_listener():
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener


def on_close():
    root.destroy()
    os._exit(0)


def main():
    global root, status_label, text_box

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
            "Privacy & Security > Accessibility, or the hotkey listener and "
            "the paste keystroke will silently do nothing."
        )

    run_hotkey_listener()

    root = tk.Tk()
    root.title("Dictation")
    root.geometry("480x280")
    root.protocol("WM_DELETE_WINDOW", on_close)

    status_label = tk.Label(root, text=IDLE_STATUS, font=("Segoe UI", 12))
    status_label.pack(pady=(16, 8))

    text_box = tk.Text(root, wrap="word", height=10, state="disabled")
    text_box.pack(fill="both", expand=True, padx=12, pady=12)

    root.mainloop()


if __name__ == "__main__":
    main()
