import json
import platform
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

CURRENT_PLATFORM = "windows" if platform.system() == "Windows" else "darwin" if platform.system() == "Darwin" else "linux"

DEFAULTS = {
    "sample_rate": 16000,
    "hotkey": {
        "windows": "ctrl_r",
        "darwin": "alt_r",
    },
    "whisper": {
        "windows": {
            "backend": "faster-whisper",
            "model_size": "small",
            "device": "cuda",
            "compute_type": "float16",
        },
        "darwin": {
            "backend": "mlx-whisper",
            "model_size": "small",
            "hf_repo": "mlx-community/whisper-small-mlx",
        },
    },
    "cleanup": {
        "backend": "local",
        "ollama_model": "llama3.2:3b",
        "ollama_url": "http://localhost:11434/api/generate",
    },
    "autostart": False,
}


def load_config():
    """Load config.json, merge with defaults, and resolve the platform-keyed
    hotkey/whisper sections down to the values for the OS this is running on.
    """
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2))
        raw = dict(DEFAULTS)
    else:
        with open(CONFIG_PATH, "r") as f:
            raw = json.load(f)

    merged = dict(DEFAULTS)
    merged.update(raw)

    if CURRENT_PLATFORM not in merged["hotkey"]:
        raise ValueError(
            f"No hotkey configured for platform '{CURRENT_PLATFORM}' in config.json "
            f"(have: {list(merged['hotkey'].keys())})"
        )
    if CURRENT_PLATFORM not in merged["whisper"]:
        raise ValueError(
            f"No whisper backend configured for platform '{CURRENT_PLATFORM}' in config.json "
            f"(have: {list(merged['whisper'].keys())})"
        )

    return {
        "sample_rate": merged["sample_rate"],
        "hotkey": merged["hotkey"][CURRENT_PLATFORM],
        "whisper": merged["whisper"][CURRENT_PLATFORM],
        "cleanup": merged["cleanup"],
        "autostart": merged["autostart"],
    }
