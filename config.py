"""Central config loader. Reads config.yaml with safe defaults."""

from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"
_BRANDS_DIR = _PROJECT_ROOT / "brands"

_DEFAULTS: dict[str, Any] = {
    "llm": {
        "provider": "openai",
        "model": "gpt-4o",
    },
    "image": {
        "hero": {
            "model": "dall-e-3",
            "size": "1792x1024",
            "quality": "hd",
            "num_variants": 3,
        },
        "inline": {
            "model": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
            "max_per_session": 2,
        },
    },
    "vision": {
        "model": "gpt-4o",
        "detail": "auto",
        "max_image_size": 2048,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


_BRAND_DEFAULTS: dict[str, Any] = {
    "name": "Default",
    "palette": {
        "primary": "#1E3A5F",
        "accent": "#00B4D8",
        "background": "#F8F9FA",
    },
    "style": "clean flat vector illustration, modern tech palette, minimal, no text",
    "tone": "professional, approachable, technical",
    "logo_path": "",
    "reference_image": "",
    "validation": {
        "enabled": True,
        "min_score": 7,
        "max_retries": 2,
    },
}


def load_config() -> dict[str, Any]:
    """Load config.yaml merged with defaults.

    Returns:
        Config dict with all keys guaranteed present via defaults.
    """
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            user_config = yaml.safe_load(f) or {}
    else:
        user_config = {}
    return _deep_merge(_DEFAULTS, user_config)


def list_brands() -> list[str]:
    """Return sorted list of brand names (filenames without .yaml) from brands/ dir.

    Returns:
        List of brand name strings.
    """
    if not _BRANDS_DIR.exists():
        return []
    return sorted(p.stem for p in _BRANDS_DIR.glob("*.yaml"))


def load_brand(name: str) -> dict[str, Any]:
    """Load a brand YAML by name, merged with brand defaults.

    Args:
        name: Brand filename without .yaml extension (e.g. 'anthropic').

    Returns:
        Brand dict with all keys guaranteed present via defaults.

    Raises:
        FileNotFoundError: If brands/<name>.yaml does not exist.
    """
    path = _BRANDS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Brand '{name}' not found at {path}")
    with open(path) as f:
        brand_data = yaml.safe_load(f) or {}
    return _deep_merge(_BRAND_DEFAULTS, brand_data)


def load_active_brand() -> dict[str, Any]:
    """Load the currently active brand from config.yaml.

    Falls back to 'corpusanalytica' if active_brand is not set or not found.

    Returns:
        Active brand dict.
    """
    cfg = load_config()
    brand_name = cfg.get("active_brand", "corpusanalytica")
    try:
        return load_brand(brand_name)
    except FileNotFoundError:
        brands = list_brands()
        if brands:
            return load_brand(brands[0])
        return dict(_BRAND_DEFAULTS)
