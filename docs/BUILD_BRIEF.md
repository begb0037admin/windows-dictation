# Build Brief: Windows Voice Dictation Assistant ("Eloquent for Windows")

## 1. Elevator pitch

A personal, system-wide voice dictation tool for Windows. Hold a hotkey, speak naturally (including "ums," false starts, self-corrections), release the hotkey, and clean, polished text is typed into whatever text box currently has focus — Teams chat, a browser, Slack, an email, anywhere. Inspired by Google AI Edge Eloquent (Mac/iOS only, not available on Windows), but built from scratch with open components — no Google code involved.

Primary use case: quick Teams messages and other short chat-box text, not long-form documents. Optimize for low latency and reliability over raw transcription accuracy.

## 2. Core user flow

1. App runs in the background with a system tray icon.
2. User places cursor in any text box (e.g., Teams message box).
3. User holds a global hotkey (e.g., `Ctrl+Win` or `CapsLock`, push-to-talk style).
4. Tray icon changes to a "recording" state; mic captures audio.
5. User releases the hotkey.
6. Audio is transcribed locally, then run through a cleanup pass (removes filler words, fixes grammar/punctuation, keeps the original meaning and tone).
7. Cleaned text is inserted at the cursor position via clipboard-paste simulation.
8. Tray icon returns to idle.

Total round-trip target: under ~3 seconds for a short sentence on a mid-range machine.

## 3. Recommended architecture

**Approach: local-first, with a cloud-cleanup toggle** (build local first — cheapest, private, no API keys needed; add cloud-swap for the cleanup step later since it's a one-line config change).

| Component | Recommendation | Why |
|---|---|---|
| Global hotkey capture | `keyboard` or `pynput` | Simple push-to-talk detection, works system-wide |
| Audio capture | `sounddevice` (records to numpy array while key is held) | Lightweight, no temp files needed |
| Speech-to-text | `faster-whisper` (local, CTranslate2-optimized Whisper), model size `base` or `small` | Free, private, fast enough on CPU; upgrade to `medium` if a GPU is available |
| Text cleanup ("de-um-ify" + grammar polish) | Local LLM via **Ollama** (e.g. `llama3.2:3b` or `gemma2:2b`) called through its local REST API | Free, private, small models are plenty for this task. Swap-in point for a cloud API (Claude/OpenAI) later — same interface, just change the function that calls the LLM |
| Text injection | Clipboard + simulated `Ctrl+V` via `pyperclip` + `pyautogui`/`pywin32` | More reliable across apps (especially Teams' web-based UI) than simulating individual keystrokes, which can drop characters or trigger autocomplete oddly |
| Tray icon / UI | `pystray` + `Pillow` for the icon | Minimal footprint, standard for this kind of always-on utility |
| Config | Simple `config.json` or `.env` — hotkey, model size, cleanup backend (local/cloud), autostart toggle |

Language: **Python**. Fast to scaffold, all the above libraries are mature and well-documented, easy for a coding agent to iterate on quickly. Package later with `pyinstaller` if a standalone `.exe` is wanted.

## 4. MVP scope (build this first)

- [ ] Push-to-talk hotkey triggers recording start/stop
- [ ] Record audio to memory while key is held
- [ ] Transcribe with faster-whisper (`base` model to start)
- [ ] Clean up transcript with a local Ollama model (strip filler words, fix grammar, preserve meaning — a short system prompt is enough)
- [ ] Paste cleaned text into the focused window via clipboard
- [ ] Tray icon with idle/recording/processing states and a quit option
- [ ] Runs on Windows 11, starts on login (optional toggle)

## 5. Stretch goals (after MVP works)

- Config UI (small settings window instead of editing JSON by hand)
- Toggle between local cleanup and a cloud LLM API for higher-quality polish
- Custom vocabulary/dictionary (e.g. project names, jargon specific to your work) fed into the Whisper prompt or a post-processing correction step
- Undo last dictation (revert clipboard/typed text with a second hotkey)
- Visual/audio feedback cue (short beep) on start/stop recording
- Silence-based auto-stop instead of pure push-to-talk
- Packaged installer (`pyinstaller` + Inno Setup) for one-click install

## 6. Known risks / gotchas to flag to the coding agent

- **Teams is often a web view (Electron/browser-based).** Clipboard-paste is much more reliable than simulated keystrokes here — confirm paste works correctly in both the Teams desktop app and Teams-in-browser.
- **First-run model download.** faster-whisper and Ollama both pull model weights on first use (hundreds of MB to a few GB) — the brief should tell the coding agent to surface download progress, not hang silently.
- **CPU-only performance.** Without a GPU, `base`/`small` Whisper models are fine for short dictation, but `medium`+ may feel sluggish — default to `base` and make it configurable.
- **Mic permissions.** Windows may block mic access for a background Python process the first time — the app should fail with a clear message, not silently record nothing.
- **Hotkey conflicts.** Pick a default hotkey unlikely to collide with existing Windows/Teams shortcuts, and make it configurable.

## 7. Suggested repo structure

```
windows-dictation/
  main.py              # tray app entry point, hotkey listener
  transcribe.py         # faster-whisper wrapper
  cleanup.py             # Ollama call + prompt for de-um-ifying/grammar fix (swap point for cloud API)
  inject.py              # clipboard + paste simulation
  config.py              # loads config.json / defaults
  config.json
  requirements.txt
  README.md
```

## 8. GPU configuration (RTX 3070, 8GB VRAM)

Machine has an RTX 3070 — plenty for this workload. Both the transcription and cleanup steps should run on GPU, and with that headroom there's no need to stay on the smallest models.

- **Whisper (faster-whisper):** set `device: cuda`, `compute_type: float16` (Ampere's tensor cores handle fp16 natively — faster and more accurate than the CPU-oriented `int8` default). Bump the model from `base` to **`small`** — still comfortably sub-second on a 3070, noticeably fewer misheard words/names than base. `medium` is an option too (~5GB VRAM) if accuracy matters more than the last bit of latency, but for short chat messages `small` is the better latency/accuracy tradeoff.
- **Ollama cleanup model:** Ollama auto-detects and uses the GPU via CUDA — no explicit device config needed, just confirm `nvidia-smi` shows the Ollama process when it's running. Keep the model itself modest (`llama3.2:3b` or `gemma2:2b`, ~2-4GB VRAM) — a bigger model doesn't meaningfully improve a one-sentence de-um-ify/grammar pass, it just adds latency. `small` Whisper (~1GB) + a 3b Ollama model (~2-4GB) leaves comfortable headroom inside 8GB VRAM even running both back-to-back.
- **Prerequisites:** NVIDIA driver + CUDA 12 + cuDNN 8 runtime libraries for faster-whisper (whisper-local's first-launch onboarding offers a one-press install of these; whisper-writer requires installing them manually — see its README's GPU section). Ollama's Windows installer bundles its own CUDA support, no separate setup needed.
- **Sanity check after setup:** run `whisper-local --doctor` (if using that fork) or watch `nvidia-smi` during a test dictation — GPU utilization should spike briefly during transcription and again during the cleanup call. If it stays at 0%, the device flag isn't being picked up and it's silently falling back to CPU.

## 9. What to hand the coding agent

Give this whole document as-is, plus: "Build the MVP checklist in section 4, in the order listed, testing each step manually before moving to the next (e.g., confirm hotkey + recording works before wiring up transcription)." That keeps the build incremental and easy to debug rather than one big untested drop.

## 10. Amendment — cross-platform (Mac + Windows), added 2026-07-09

Original brief scoped Windows only. Kevin confirmed after Step 1 was built that this needs to run on **both** his Windows machine (RTX 3070) and a Mac (**Apple Silicon**, confirmed) — one unified codebase, not two separate apps.

**What changes from the sections above:**

| Component | Section 3 original | Cross-platform revision |
|---|---|---|
| Global hotkey capture | `keyboard`/`pynput` | **`pynput` only.** The `keyboard` library is Windows/Linux-oriented and unreliable on macOS. `pynput` works on both. |
| Hotkey choice | `Ctrl+Win` or `CapsLock` | **A lone modifier key** (Right Ctrl on Windows, Right Option on Mac) instead of Caps Lock. Caps Lock has OS-level toggle behaviour on both platforms that fights with push-to-talk hold detection and needs suppression, which `pynput` can't do selectively (its `suppress=True` blocks *all* system input, not just the one key). A modifier key held alone has no side effects on either OS, so no suppression is needed at all. |
| Speech-to-text | faster-whisper (all platforms) | **Per-platform backend.** faster-whisper (CTranslate2) has no Metal/MPS acceleration — on Apple Silicon it would run CPU-only. Use faster-whisper + CUDA on Windows (unchanged, see §8) and **`mlx-whisper`** on Mac — Apple's MLX framework, Metal-accelerated, comparable latency to the Windows GPU path on M-series chips. |
| Cleanup LLM | Ollama | **Unchanged.** Ollama runs natively accelerated on both platforms (CUDA on Windows, Metal on Apple Silicon) with no extra config. |
| Text injection | `pyperclip` + `pyautogui`/`pywin32` | **`pyperclip` + `pyautogui`, no `pywin32`.** `pywin32` is Windows-only; `pyautogui` covers the paste keystroke on both platforms. Paste key differs: `Ctrl+V` on Windows, `Cmd+V` on Mac — detect via `platform.system()`. macOS additionally requires the app be granted **Accessibility** and **Input Monitoring** permission (System Settings → Privacy & Security) for both the hotkey listener and the paste simulation to work at all — this has no Windows equivalent and should fail with a clear message, not silently do nothing. |
| Tray icon | `pystray` + `Pillow` | **Unchanged** — pystray supports the Windows system tray and the macOS menu bar with the same API. |
| Config | Single `config.json` | **Platform-keyed sections** for hotkey and whisper backend (`windows` / `darwin`), auto-selected by `platform.system()` at load time, with a shared config layer for everything else (sample rate, Ollama settings, autostart). |

**Still local-first, still no cloud dependency in the MVP** — this amendment is about running the same behaviour on two OSes, not about adding a server component.
