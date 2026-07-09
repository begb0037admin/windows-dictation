# windows-dictation — Living Handover Document

**Last updated:** 2026-07-09 (Kevin session) — scope widened to cross-platform (Windows + Mac); Step 1 rebuilt accordingly
**Status:** MVP Step 1 (hotkey + recording) rebuilt cross-platform, awaiting Kevin's test on both machines

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
