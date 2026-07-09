# Windows Dictation

Personal, system-wide voice dictation assistant for Windows ("Eloquent for Windows").

Hold a hotkey, speak naturally (ums, false starts, self-corrections included), release — clean, polished text is typed into whatever text box has focus: Teams chat, browser, email, anywhere.

**Primary use case:** quick Teams messages and short chat-box text. Optimised for low latency and reliability over raw transcription accuracy. Target round-trip: under ~3 seconds for a short sentence.

## How it works

1. App runs in the background with a system tray icon
2. Place cursor in any text box
3. Hold the global hotkey (push-to-talk); mic records while held
4. Release — audio is transcribed locally (faster-whisper), then cleaned up by a local LLM (Ollama): filler words stripped, grammar fixed, meaning and tone preserved
5. Cleaned text is pasted at the cursor via clipboard simulation

## Architecture

| Component | Choice |
|---|---|
| Language | Python |
| Hotkey capture | `keyboard` / `pynput` |
| Audio capture | `sounddevice` (in-memory numpy) |
| Speech-to-text | `faster-whisper` — `small` model on GPU (CUDA, fp16) |
| Text cleanup | Ollama local REST API (`llama3.2:3b` or `gemma2:2b`) — swap point for a cloud API later |
| Text injection | Clipboard + simulated Ctrl+V (`pyperclip` + `pyautogui`/`pywin32`) |
| Tray icon | `pystray` + `Pillow` |
| Config | `config.json` — hotkey, model size, cleanup backend, autostart |

Local-first: free, private, no API keys. Target machine has an RTX 3070 (8GB VRAM) — both transcription and cleanup run on GPU. See `docs/BUILD_BRIEF.md` §8 for GPU configuration.

## Status

MVP build in progress — building `docs/BUILD_BRIEF.md` §4 checklist in order, testing each step on Kevin's Windows machine before moving to the next.

- [x] **Step 1** — Push-to-talk hotkey (Caps Lock) triggers recording start/stop; audio captured to memory; tray icon (grey idle / red recording)
- [ ] Step 2 — Transcribe with faster-whisper
- [ ] Step 3 — Clean up transcript with local Ollama model
- [ ] Step 4 — Paste cleaned text at cursor via clipboard
- [ ] Step 5 — Run on login (optional toggle)

### Running Step 1

```
pip install -r requirements.txt
python main.py
```

Hold **Caps Lock**, speak, release. The console prints how many seconds of audio were captured — nothing is transcribed yet. A tray icon shows idle (grey) / recording (red) state; right-click to Quit.

On Windows, global hotkey hooking via the `keyboard` library usually requires running the terminal **as Administrator**. If the mic can't be opened, check Settings → Privacy & security → Microphone and allow desktop apps.

Hotkey and sample rate are configurable in `config.json`.

## Repo structure

```
main.py           # tray app entry point, hotkey listener, audio capture (Step 1 — done)
config.py         # loads config.json / defaults
config.json
requirements.txt
transcribe.py     # faster-whisper wrapper (Step 2 — not yet built)
cleanup.py        # Ollama call + de-um-ify/grammar prompt (Step 3 — not yet built)
inject.py         # clipboard + paste simulation (Step 4 — not yet built)
docs/BUILD_BRIEF.md
CLAUDE.md / AGENT_MODEL.md / CONSTITUTION.md / HANDOVER.md   # governance stack
```
