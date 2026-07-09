# Dictation

Personal, system-wide voice dictation assistant for **Windows and Mac** ("Eloquent," unified across both).

Hold a hotkey, speak naturally (ums, false starts, self-corrections included), release — clean, polished text is typed into whatever text box has focus: Teams chat, browser, email, anywhere. One codebase, same behaviour on both machines.

**Primary use case:** quick Teams messages and short chat-box text. Optimised for low latency and reliability over raw transcription accuracy. Target round-trip: under ~3 seconds for a short sentence.

## How it works

1. App runs in the background with a system tray icon (Windows tray / macOS menu bar)
2. Place cursor in any text box
3. Hold the global hotkey (push-to-talk); mic records while held
4. Release — audio is transcribed locally, then cleaned up by a local LLM (Ollama): filler words stripped, grammar fixed, meaning and tone preserved
5. Cleaned text is pasted at the cursor via clipboard simulation

## Architecture

| Component | Windows | Mac (Apple Silicon) |
|---|---|---|
| Language | Python (shared codebase) | Python (shared codebase) |
| Hotkey capture | `pynput` — Right Ctrl by default | `pynput` — Right Option by default |
| Audio capture | `sounddevice` (in-memory numpy) | `sounddevice` (in-memory numpy) |
| Speech-to-text | `faster-whisper`, `small` model, CUDA + fp16 (RTX 3070) | `mlx-whisper`, `small` model, Metal-accelerated |
| Text cleanup | Ollama local REST API (`llama3.2:3b` / `gemma2:2b`) — swap point for a cloud API later | Same — Ollama auto-accelerates via Metal |
| Text injection | Clipboard + simulated `Ctrl+V` (`pyperclip` + `pyautogui`) | Clipboard + simulated `Cmd+V` (`pyperclip` + `pyautogui`) |
| Tray icon | `pystray` + `Pillow` — system tray | `pystray` + `Pillow` — menu bar |
| Config | `config.json` — platform-keyed hotkey/whisper sections, shared cleanup/sample-rate settings | same file |

Local-first: free, private, no API keys. See `docs/BUILD_BRIEF.md` §8 for the original Windows GPU configuration and §10 for the cross-platform amendment (backend choices, why Caps Lock was dropped in favour of a modifier key, macOS permission requirements).

## Status

MVP build in progress — building `docs/BUILD_BRIEF.md` §4 checklist in order, testing each step on both machines before moving to the next.

- [x] **Step 1** — Push-to-talk hotkey (Right Ctrl / Right Option) triggers recording start/stop; audio captured to memory; tray icon (grey idle / red recording). Cross-platform via `pynput`. **Confirmed working on both Windows (7.75s capture) and Mac (19.79s capture).**
- [x] **Step 2** — Transcribe: `faster-whisper` + CUDA on Windows, `mlx-whisper` on Mac. **Confirmed working on Windows** (accurate transcript after installing the CUDA runtime via pip — see below). Mac was verified once in isolation; needs a fresh test now that Step 3 is wired in.
- [x] **Step 3** — Clean up the transcript via a local Ollama model (`llama3.2:3b`), strips fillers/fixes grammar while preserving meaning. **Confirmed working on Windows** after fixing a prompt bug where the model responded conversationally to request-like transcripts instead of editing them. Mac untested.
- [ ] Step 4 — Paste cleaned text at cursor via clipboard
- [ ] Step 5 — Run on login (optional toggle)

### Running Step 1

```
pip install -r requirements.txt
python main.py
```

Hold the hotkey (**Right Ctrl** on Windows, **Right Option** on Mac by default), speak, release. The console prints how many seconds of audio were captured — nothing is transcribed yet. A tray icon/menu-bar icon shows idle (grey) / recording (red) state; right-click (Windows) or click (Mac) to Quit.

**Windows:** global hotkey hooking usually requires running the terminal **as Administrator**. If the mic can't be opened, check Settings → Privacy & security → Microphone and allow desktop apps.

**Mac:** grant **Accessibility** permission to Terminal (or your Python interpreter) under System Settings → Privacy & Security → Accessibility — without it, `pynput` silently receives no key events at all. If the mic can't be opened, grant Microphone access in the same Privacy & Security pane.

Hotkey (per platform), sample rate, and whisper backend are all configurable in `config.json`.

## Repo structure

```
main.py           # tray app entry point, hotkey listener, audio capture (Step 1 — done, cross-platform)
config.py         # loads config.json / defaults, resolves platform-keyed sections
config.json
requirements.txt
transcribe.py     # faster-whisper / mlx-whisper wrapper (Step 2 — not yet built)
cleanup.py        # Ollama call + de-um-ify/grammar prompt (Step 3 — not yet built)
inject.py         # clipboard + paste simulation (Step 4 — not yet built)
docs/BUILD_BRIEF.md
CLAUDE.md / AGENT_MODEL.md / CONSTITUTION.md / HANDOVER.md   # governance stack
```
