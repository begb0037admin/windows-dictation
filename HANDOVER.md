# windows-dictation — Living Handover Document

**Last updated:** 2026-07-09 (Kevin session) — repo created, governance stack added, MVP build starting
**Status:** New — Step 1 of MVP (hotkey + recording) in progress

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
