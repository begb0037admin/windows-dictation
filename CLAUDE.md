# CLAUDE.md — windows-dictation
> AI bootstrap entry point. Read this first.
> Keep this file under 200 lines. Push details to linked docs.

## Identity
- **Project:** Windows Dictation — system-wide push-to-talk voice dictation assistant for Windows
- **Purpose:** Hold a hotkey, speak naturally, release — cleaned-up text (fillers stripped, grammar fixed, meaning preserved) is pasted into whatever text box has focus. Built for quick Teams messages and short chat-box text.
- **Owner:** Kevin Lelitte, Manager/Director HR Systems, University of Oxford
- **Status:** New — brief written, MVP not yet started
- **Repo:** https://github.com/begb0037admin/windows-dictation
- **Runs on:** Kevin's Windows 11 machine (RTX 3070, 8GB VRAM) — local-only, no cloud dependencies in MVP

## Bootstrap Order
1. This file (orientation)
2. `AGENT_MODEL.md` and `CONSTITUTION.md` — governance and role model (cross-repo standard)
3. `HANDOVER.md` — current state, what was just built, what's next
4. `docs/BUILD_BRIEF.md` — the full build brief; the source of truth for scope, architecture, and MVP build order
5. `README.md` — condensed overview

Do NOT ask Kevin for a recap. HANDOVER.md is the recap.

## Build Order
Build the MVP checklist in `docs/BUILD_BRIEF.md` §4, in the order listed, testing each step manually before moving to the next (confirm hotkey + recording works before wiring up transcription, etc.). Incremental and debuggable — not one big untested drop.

## Architecture
| Component | Choice |
|---|---|
| `main.py` | Tray app entry point, hotkey listener |
| `transcribe.py` | faster-whisper wrapper — `small` model, `device: cuda`, `compute_type: float16` |
| `cleanup.py` | Ollama local REST API (`llama3.2:3b` / `gemma2:2b`) — the swap point for a cloud LLM later |
| `inject.py` | Clipboard + simulated Ctrl+V paste |
| `config.py` / `config.json` | Hotkey, model size, cleanup backend (local/cloud), autostart |

## Key Constraints
- Local-first: no API keys, no cloud calls in MVP. Cloud cleanup is a later config toggle.
- Clipboard-paste injection, NOT simulated keystrokes — Teams' web view drops simulated keystrokes. Verify paste in both Teams desktop and Teams-in-browser.
- GPU: transcription and cleanup both run on the RTX 3070. Sanity-check with `nvidia-smi` — 0% GPU during a test dictation means silent CPU fallback.
- Surface model-download progress on first run (faster-whisper + Ollama pull hundreds of MB) — never hang silently.
- Fail loudly with a clear message if Windows blocks mic access — never silently record nothing.
- Default hotkey must avoid Windows/Teams shortcut collisions and be configurable.

## Effort Level Governance
Before any task where higher effort is warranted, signal to Kevin: what the task is, why higher effort is needed, and an explicit request to raise the effort level. Wait — do not proceed until Kevin raises it. Signal when the high-effort phase is done; Kevin decides when to return to normal. Never change effort level unilaterally. See CONSTITUTION.md Section 10 (v2.0, 2026-06-27).

## Hard Rules
- Never commit credentials or API keys — the MVP needs none; if a cloud cleanup toggle is added later, keys live in env vars only
- The brief (`docs/BUILD_BRIEF.md`) defines scope — do not add stretch goals (§5) before the MVP checklist (§4) is complete and working
- Build and test one MVP checklist item at a time — Kevin confirms each step works on his Windows machine before the next is built
- This is a local Windows app — Claude Code writes and pushes the code but cannot run or test it (no mic, no hotkey listener, no GPU in the cloud sandbox); Kevin runs and verifies on the admin machine
- Always update `HANDOVER.md` at end of session
- All mockups and visual designs are produced as Claude Artifacts — never committed to the repository (see CONSTITUTION.md Section 11)

## Branch and Merge Protocol
Always push directly to main. If a branch must be used, merge it to main immediately upon completion — never leave files on a branch.
