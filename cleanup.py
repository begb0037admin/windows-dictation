"""
Step 3 of the MVP: clean up the raw transcript via a local Ollama model.
Strips filler words ("um", "uh", false starts), fixes grammar/punctuation,
preserves the original meaning and tone. Swap point for a cloud LLM later —
same interface, just point cleanup_config at a different backend.

Ollama runs natively accelerated on both platforms (CUDA on Windows, Metal
on Apple Silicon) with no extra config needed here.
"""

import json
import urllib.error
import urllib.request

SYSTEM_PROMPT = (
    "You clean up raw speech-to-text transcripts for a chat message. "
    "Remove filler words (um, uh, like), false starts, and self-corrections. "
    "Fix grammar and punctuation. Preserve the original meaning, wording "
    "choices, and tone as closely as possible — do not rephrase, summarize, "
    "or add anything that wasn't said. Reply with ONLY the cleaned-up text, "
    "no preamble, no quotes, no explanation."
)


def cleanup(text: str, cleanup_config: dict) -> str:
    """Run a raw transcript through the local Ollama cleanup pass."""
    if not text.strip():
        return text

    payload = json.dumps(
        {
            "model": cleanup_config["ollama_model"],
            "system": SYSTEM_PROMPT,
            "prompt": text,
            "stream": False,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        cleanup_config["ollama_url"],
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"[cleanup] could not reach Ollama at {cleanup_config['ollama_url']} "
            f"— is Ollama running? ({exc})"
        ) from exc

    if "error" in result:
        raise RuntimeError(
            f"[cleanup] Ollama error: {result['error']} — if this is a missing "
            f"model, run: ollama pull {cleanup_config['ollama_model']}"
        )

    return result["response"].strip()
