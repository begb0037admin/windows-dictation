# windows-dictation — Living Handover Document

**Last updated:** 2026-07-09 — Claude Code now running locally on the admin machine; Step 3 (Ollama cleanup) built and pushed
**Status:** Step 1 confirmed on both platforms. Step 2 (transcription) confirmed working on Windows; Mac side still untested. Step 3 (Ollama cleanup) built and pushed — untested on both platforms (Ollama not yet installed on the admin machine).

---

## Session 2026-07-09 (continued) — Claude Code now running locally; Step 3 built

**Environment change confirmed:** this session is running as Claude Code directly on the admin machine (`whoami` → `admin`, `hostname` → `DESKTOP-MJDJM64`, `nvidia-smi` shows the real RTX 3070), not in a cloud sandbox. This matches the recommendation logged in the previous session (install Claude Code locally so an agent can drive remaining steps directly instead of manual copy-paste relay). Practical effect: Claude Code can now run local commands and inspect real output on this machine directly — though the hotkey/mic flow still needs Kevin to physically hold the key and speak.

**Flag for Kevin:** `CLAUDE.md`'s Hard Rules still say "Claude Code cannot run or test it (no mic, no hotkey listener, no GPU in the cloud sandbox)" — that assumption no longer holds for the Windows side now that Claude Code runs locally. Not changed unilaterally; flagging for you to confirm/update that rule.

**Step 3 built:** `cleanup.py` — calls the local Ollama REST API (`/api/generate`, non-streaming) with a system prompt that strips filler words/false starts and fixes grammar while preserving meaning and tone; returns the cleaned text only. Uses `urllib.request` (stdlib), no new dependency added. Raises a clear error if Ollama isn't reachable, or if the configured model (`llama3.2:3b` per `config.json`) isn't pulled yet (`ollama pull llama3.2:3b`). Wired into `main.py`: after a successful transcription, `stop_recording()` now also calls `cleanup()` and prints the cleaned result. No text injection yet (Step 4, still next).

**Not tested:** Ollama isn't installed on this admin machine yet (`where ollama` and a request to `localhost:11434` both came back empty; winget confirms `Ollama.Ollama` is available to install). Mac side is also untested. Two things need Kevin's decision before this is verified:
1. Install Ollama on the admin machine — Claude Code can now do this directly via `winget install Ollama.Ollama` given local execution, or Kevin can do it himself. Awaiting a decision since installing software wasn't previously in Claude Code's scope on this machine.
2. Once installed, `ollama pull llama3.2:3b` needs to run once, then Step 3 can be exercised end-to-end alongside a real dictation (or with a canned transcript for a quick isolated check of `cleanup.py` alone).

`.gitignore` added (`__pycache__/`, `*.pyc`, and `rundictation.bat` — the latter is a personal convenience script delivered via SendUserFile, never meant to be committed).

**Next action:** Kevin decides on Ollama install method; once cleanup.py is verified on Windows, same for Mac; then Step 4 (clipboard + paste injection) gets built.

---

## Session 2026-07-09 (continued) — Step 1 confirmed on Mac; Step 2 built

**Mac setup hit a real environment issue, resolved:** Kevin's Mac shipped with the old Apple Command Line Tools Python (3.9.6), which has no prebuilt wheel for `pyobjc-core` (a `pynput` dependency on macOS) and failed compiling it from source — a known incompatibility (that pyobjc release is flagged "yanked" for wrongly claiming Python 3.9 support). Fix: installed Python 3.14.6 from python.org, which has prebuilt wheels for everything. `pip3.14 install -r requirements.txt` then succeeded cleanly.

**Step 1 result on Mac:** held Right Option, console reported `316584 samples, 19.79s captured at 16000Hz`. Confirmed working on both platforms now.

**Step 2 built:** `transcribe.py` — lazy-loads and caches the model on first call. `faster-whisper` (`small`, CUDA, fp16) on Windows; `mlx-whisper` on Mac, repo id `mlx-community/whisper-small-mlx` (set in `config.json`'s Mac `whisper` section, **not yet verified against the actual Hugging Face repo** — if the first run 404s trying to download, this needs correcting to whatever the real repo slug is). `main.py` now calls `transcribe()` after every recording and prints the raw transcript — no cleanup, no injection yet.

`requirements.txt` updated with platform markers: `faster-whisper; sys_platform == "win32"` and `mlx-whisper; sys_platform == "darwin"`.

**Windows Step 2 confirmed working** (after one more environment fix): `faster-whisper` needs the CUDA 12 runtime libraries (cuBLAS + cuDNN) — having the NVIDIA driver alone isn't enough, and the full CUDA Toolkit installer is multi-GB overkill. Fixed by installing the runtime as pip packages instead:
```
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```
then adding their `bin` folders to the Windows user PATH (via System Properties → Environment Variables → User variables → Path):
- `C:\Users\admin\AppData\Roaming\Python\Python314\site-packages\nvidia\cublas\bin`
- `C:\Users\admin\AppData\Roaming\Python\Python314\site-packages\nvidia\cudnn\bin`

Confirmed persistent across a fresh PowerShell window (no `$env:PATH` override needed). Real transcript came back accurate for an 11.83s recording.

**Not yet done:** Mac side of Step 2 (mlx-whisper) hasn't been tested — still pending, including verifying the `mlx-community/whisper-small-mlx` repo id is actually correct.

**Workflow note (2026-07-09):** Kevin flagged that relaying every test through copy-pasted terminal output is inefficient — correct. This cloud session has no direct access to either of Kevin's machines. Recommended he install Claude Code locally on the Windows machine (matches `AGENT_MODEL.md` Section 1, which already documents "Admin machine (Kevin): Runs Claude Code (primary agent)" as the intended model across his other repos) so an agent can drive the remaining steps directly instead of through manual relay. Awaiting Kevin's decision on this before continuing Step 3.

---

## Session 2026-07-09 (continued) — Step 1 confirmed on Windows

**Result:** Kevin ran `main.py` on the Windows machine (RTX 3070), held Right Ctrl for ~8 seconds while speaking, released — console reported `123968 samples, 7.75s captured at 16000Hz`. Recording start/stop and audio capture to memory both work correctly.

**Debugging along the way (kept here for reference, not because it's still relevant):**
- First confusion was environment/working-directory related (running `python main.py` from `C:\Users\admin` instead of the cloned repo folder) — resolved.
- Added a temporary debug print on every keypress to check pynput was receiving events at all and to identify the exact key name for "Right Ctrl" on Kevin's keyboard. Confirmed `<Key.ctrl_r: <163>>` maps correctly and Left Ctrl (`ctrl_l`) is correctly ignored.
- Windows fires repeated key-down (auto-repeat) events for a physically held key — this looked like a runaway bug the first time but is normal OS behaviour; `start_recording()`/`stop_recording()` already guard against duplicate calls, so it was cosmetic only (spammed the debug log, nothing else).
- Debug logging removed once confirmed working — `main.py` is back to clean Step 1 code.
- Delivered `run-dictation.bat` (via SendUserFile, not committed to the repo — it's a personal convenience script, not part of the app) so Kevin can `cd` + `git pull` + `python main.py` with one double-click instead of typing commands each time.

**Next action:** Kevin runs the same test on the Mac (Apple Silicon) — hold **Right Option**, confirm the same kind of console output. Once both platforms are confirmed, Step 2 (transcription — faster-whisper on Windows, mlx-whisper on Mac) gets built.

---

## Session 2026-07-09 (continued) — Cross-platform pivot

**What happened:**
Kevin confirmed after Step 1 was first built (Windows-only) that this needs to be unified across Windows and Mac — one codebase, not two apps. Confirmed Mac hardware: **Apple Silicon**.

**Amendment recorded:** `docs/BUILD_BRIEF.md` §10 — full rationale for each component swap.

**Changes made:**
- Hotkey library: `keyboard` → **`pynput`** (the `keyboard` library doesn't work reliably on macOS)
- Default hotkey: Caps Lock → **Right Ctrl (Windows) / Right Option (Mac)** — modifier keys held alone have no OS side effects, so no key-suppression is needed (which `pynput` can't do selectively — its `suppress=True` blocks all system input, not just one key)
- `config.json` restructured with platform-keyed `hotkey` and `whisper` sections (`windows` / `darwin`), resolved by `platform.system()` in `config.py` at load time
- Whisper backend, planned for Step 2: **faster-whisper + CUDA** on Windows (unchanged), **mlx-whisper** on Mac (Metal-accelerated — faster-whisper has no Apple Silicon GPU support)
- Text injection, planned for Step 4: `pyperclip` + `pyautogui` on both; paste key `Ctrl+V` (Windows) vs `Cmd+V` (Mac); `pywin32` dropped (Windows-only)
- `main.py`, `config.py`, `config.json`, `requirements.txt`, `README.md`, `CLAUDE.md` all updated for the new scope

**Not done:** repo is still named `windows-dictation` — flagged to Kevin as a possible rename candidate, not renamed unilaterally.

**Next action:** Kevin tests Step 1 on **both** the Windows machine and the Mac (`pip install -r requirements.txt && python main.py`, hold Right Ctrl/Right Option, confirm console reports a sane capture duration on each). Mac needs Accessibility permission granted to Terminal first. Once both are confirmed working, Step 2 (transcription, per-platform backend) gets built.

---

## Session 2026-07-09 — Repo created, governance stack added

**What happened:**
- Repo `begb0037admin/windows-dictation` created (private) at Kevin's request, from `docs/BUILD_BRIEF.md` (the original build brief, committed verbatim).
- Standard governance stack added to match the estate template (`clockify` is the gold standard):
  - `CONSTITUTION.md` v2.1 — copied verbatim (cross-repo, unmodified)
  - `AGENT_MODEL.md` v2.5 — copied with local annotations only (Section 1, Section 7, Section 8 row) noting this repo runs locally on Kevin's Windows machine, not via GitHub Pages
  - `HANDOVER.md` (this file) — session record
  - `README.md` — condensed project overview
  - `CLAUDE.md` — bootstrap entry point, updated to point at the standard docs
- **Not done:** the shared `AGENT_MODEL.md` Section 8 repository table in the *other* 10 repos was not updated to list `windows-dictation`. That's a separate propagation operation across the whole estate — flag to Kevin if full cross-repo visibility is wanted.

**Next action:** Build MVP Step 1 (push-to-talk hotkey + audio capture to memory) per `docs/BUILD_BRIEF.md` §4 and §9 — build and test one step at a time, Kevin confirms each step works on his Windows/RTX 3070 machine before the next step is built.

---

## Architecture

| Component | Description |
|---|---|
| `docs/BUILD_BRIEF.md` | Original build brief — source of truth for scope, architecture, and MVP order |
| `main.py` | Tray app entry point, hotkey listener, audio capture |
| `config.py` / `config.json` | Hotkey, model, and backend configuration |
| `transcribe.py` | faster-whisper wrapper (not yet built — Step 3) |
| `cleanup.py` | Ollama cleanup call (not yet built — Step 4) |
| `inject.py` | Clipboard + paste injection (not yet built — Step 5) |

## Key Constraints
- This is a **local Windows app** — it needs a mic, a global hotkey listener, and (ideally) Kevin's RTX 3070 GPU. Claude Code cannot run or test it directly; code is written and pushed to GitHub, then run and verified by Kevin on the admin machine.
- Build order is sequential and gated: each MVP checklist item (`docs/BUILD_BRIEF.md` §4) is tested manually on Kevin's machine before the next is built.

## Next Action
Build Step 1 of the MVP: `main.py` with tray icon + CapsLock push-to-talk hotkey + audio capture to memory (no transcription yet). Kevin runs it locally and confirms the hotkey triggers recording start/stop correctly before Step 2 (transcription) is built.
