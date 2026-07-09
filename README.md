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

Not yet built — MVP scope and build order are defined in `docs/BUILD_BRIEF.md` §4. Build the checklist in order, testing each step manually before moving to the next.

## Repo structure (planned)

```
main.py           # tray app entry point, hotkey listener
transcribe.py     # faster-whisper wrapper
cleanup.py        # Ollama call + de-um-ify/grammar prompt (cloud swap point)
inject.py         # clipboard + paste simulation
config.py         # loads config.json / defaults
config.json
requirements.txt
docs/BUILD_BRIEF.md
```
