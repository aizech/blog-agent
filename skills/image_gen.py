"""Image generation for blog posts.

Supports OpenAI DALL-E 2/3 and GPT image models (gpt-image-1, gpt-image-1.5, gpt-image-2).
DALL-E models return URLs; GPT image models return base64 JSON.
"""

import base64
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import OpenAI

_GPT_IMAGE_MODELS = {"gpt-image-1", "gpt-image-1.5", "gpt-image-2", "gpt-image-1-mini"}

# Allow importing config from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import load_config

_cfg = load_config()["image"]
_HERO_CFG = _cfg["hero"]
_INLINE_CFG = _cfg["inline"]

OUTPUT_IMAGES = Path(__file__).resolve().parent.parent / "output" / "images"
OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)

# In-memory session counters
_session_state = {"inline_count": 0, "style_tag": None}


def _get_client() -> OpenAI:
    """Get OpenAI client. API key from env or .env."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _save_image_from_url(image_url: str, filename: str) -> str:
    """Download an image from a URL and save it locally (DALL-E models).

    Args:
        image_url: URL of the generated image.
        filename: Local filename to save as.

    Returns:
        Absolute path to saved file.
    """
    import requests
    resp = requests.get(image_url, timeout=30)
    resp.raise_for_status()
    path = OUTPUT_IMAGES / filename
    path.write_bytes(resp.content)
    return str(path.resolve())


def _save_image_from_b64(b64_data: str, filename: str) -> str:
    """Decode base64 image data and save locally (GPT image models).

    Args:
        b64_data: Base64-encoded image string.
        filename: Local filename to save as.

    Returns:
        Absolute path to saved file.
    """
    path = OUTPUT_IMAGES / filename
    path.write_bytes(base64.b64decode(b64_data))
    return str(path.resolve())


def _is_gpt_image_model(model: str) -> bool:
    """Return True if model is a GPT image model (not DALL-E)."""
    return model in _GPT_IMAGE_MODELS or model.startswith("gpt-image")


def derive_style_tag(
    topic: str,
    tone_preset: str = "default",
    brand_kit: Optional[dict] = None,
) -> str:
    """Derive a consistent style tag for all images in this session.

    If brand_kit is provided, its style and palette take precedence over tone_preset.
    Stored in _session_state so all subsequent images share the same style.

    Args:
        topic: Blog post topic.
        tone_preset: Tone preset influencing image style (fallback when no brand_kit).
        brand_kit: Optional brand dict from config.load_brand().

    Returns:
        Style descriptor string.
    """
    if brand_kit:
        palette = brand_kit.get("palette", {})
        palette_desc = (
            f"{palette.get('primary', '')} / {palette.get('accent', '')} / "
            f"{palette.get('background', '')}"
        ).strip(" /")
        brand_style = brand_kit.get("style", "")
        brand_tone = brand_kit.get("tone", "")
        style = (
            f"Brand: {brand_kit.get('name', '')}. "
            f"Palette: {palette_desc}. "
            f"Style: {brand_style}. "
            f"Tone: {brand_tone}."
        )
    else:
        base_styles = {
            "default": "clean flat vector illustration, modern tech palette (slate blue / warm gray / white), "
                       "minimal composition, no text, professional but approachable",
            "executive": "sleek isometric illustration, corporate color palette (navy / teal / white), "
                         "clean lines, professional, no text",
            "tutorial": "friendly illustrated style, warm tones (amber / soft teal / white), "
                        "clear visual hierarchy, no text",
            "deep-dive": "detailed technical illustration, dark mode palette (charcoal / electric blue / cyan), "
                         "complex composition, no text",
        }
        style = base_styles.get(tone_preset, base_styles["default"])
    style = f"Topic: {topic}. {style}"
    _session_state["style_tag"] = style
    return style


def reset_session():
    """Reset image session counters (call at start of each generation)."""
    _session_state["inline_count"] = 0
    _session_state["style_tag"] = None


def get_remaining_inline_slots() -> int:
    """How many more inline images can be generated this session (max config)."""
    return max(0, _INLINE_CFG["max_per_session"] - _session_state["inline_count"])


def generate_hero_image(
    topic: str,
    tone_preset: str = "default",
    num_variants: int = 3,
    brand_kit: Optional[dict] = None,
    session_timestamp: Optional[str] = None,
) -> dict:
    """Generate hero image variant(s). Returns dict with variants list.

    Each variant: {path, url, alt_text, prompt_used, variant_index}

    Args:
        topic: Blog post topic.
        tone_preset: Tone preset for style.
        num_variants: Number of variants to generate (default 3).
        brand_kit: Optional brand configuration.
        session_timestamp: Optional timestamp string for consistent filenames (e.g., "20250110_143022").

    Returns:
        Dict with 'variants' list.
    """
    style_tag = derive_style_tag(topic, tone_preset, brand_kit)
    client = _get_client()
    variants = []

    prompt = (
        f"Hero image for a technical blog post about: {topic}. "
        f"{style_tag}. "
        f"Wide landscape composition, suitable as a page header. "
        f"Useful negative space on sides for text overlay. "
        f"No text, no watermark, no logos."
    )

    model = _HERO_CFG["model"]
    use_gpt = _is_gpt_image_model(model)
    output_fmt = _HERO_CFG.get("output_format", "png")
    ext = output_fmt if output_fmt in {"png", "webp", "jpeg"} else "png"

    for i in range(num_variants):
        try:
            kwargs: dict = {
                "model": model,
                "prompt": prompt,
                "size": _HERO_CFG["size"],
                "quality": _HERO_CFG["quality"],
                "n": 1,
            }
            if use_gpt:
                kwargs["output_format"] = output_fmt
                if _HERO_CFG.get("background"):
                    kwargs["background"] = _HERO_CFG["background"]

            resp = client.images.generate(**kwargs)
            ts = session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hero-{ts}-v{i+1}.{ext}"

            if use_gpt:
                b64 = resp.data[0].b64_json
                path = _save_image_from_b64(b64, filename)
                revised_prompt = prompt
                image_url = None
            else:
                image_url = resp.data[0].url
                revised_prompt = getattr(resp.data[0], "revised_prompt", None) or prompt
                path = _save_image_from_url(image_url, filename)

            # Clean topic for alt text (remove author names, dates, publication names)
            clean_topic = topic
            # Remove common patterns like "| by Author Name |", "| Date |", "— Author Name"
            import re
            clean_topic = re.sub(r'\s*[\|—-]\s*(by\s+)?[^|]+\|\s*\w+[,\s]+\d{4}\s*\|.*$', '', clean_topic)
            clean_topic = re.sub(r'\s*[\|—-]\s*\w+[,\s]+\d{4}\s*$', '', clean_topic)
            clean_topic = re.sub(r'\s*[\|—-]\s*by\s+[^|]+$', '', clean_topic)
            clean_topic = re.sub(r'\s*[\|—-]\s*[^|]+$', '', clean_topic)
            clean_topic = clean_topic.strip()

            variants.append({
                "path": path,
                "url": image_url,
                "alt_text": f"Hero image: {clean_topic}",
                "prompt_used": revised_prompt,
                "variant_index": i,
            })
        except Exception as e:
            variants.append({
                "path": None,
                "url": None,
                "alt_text": f"Failed to generate hero variant {i+1}",
                "error": str(e),
                "variant_index": i,
            })

    return {"variants": variants, "style_tag": style_tag}


def generate_inline_image(
    topic: str,
    section_context: str,
    brand_kit: Optional[dict] = None,
    session_timestamp: Optional[str] = None,
) -> dict:
    """Generate one inline image. Enforces max 2 per session.

    Args:
        topic: Blog post topic.
        section_context: What this image should illustrate (e.g., "database indexing diagram").
        brand_kit: Optional brand configuration.
        session_timestamp: Optional timestamp string for consistent filenames (e.g., "20250110_143022").

    Returns:
        Dict with path, url, alt_text.
    """
    # Enforce cap
    if _session_state["inline_count"] >= _INLINE_CFG["max_per_session"]:
        return {
            "path": None,
            "url": None,
            "alt_text": f"Max inline images reached ({_INLINE_CFG['max_per_session']})",
            "error": "INLINE_CAP_REACHED",
        }

    style_tag = _session_state.get("style_tag") or derive_style_tag(topic, brand_kit=brand_kit)
    client = _get_client()

    prompt = (
        f"Illustration for a blog section about: {section_context}. "
        f"From a blog post about: {topic}. "
        f"{style_tag}. "
        f"Square composition, no text, no watermark, no logos."
    )

    model = _INLINE_CFG["model"]
    use_gpt = _is_gpt_image_model(model)
    output_fmt = _INLINE_CFG.get("output_format", "png")
    ext = output_fmt if output_fmt in {"png", "webp", "jpeg"} else "png"

    try:
        kwargs: dict = {
            "model": model,
            "prompt": prompt,
            "size": _INLINE_CFG["size"],
            "quality": _INLINE_CFG["quality"],
            "n": 1,
        }
        if use_gpt:
            kwargs["output_format"] = output_fmt
            if _INLINE_CFG.get("background"):
                kwargs["background"] = _INLINE_CFG["background"]

        resp = client.images.generate(**kwargs)
        ts = session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inline-{ts}-{_session_state['inline_count']+1}.{ext}"

        if use_gpt:
            b64 = resp.data[0].b64_json
            path = _save_image_from_b64(b64, filename)
            revised_prompt = prompt
            image_url = None
        else:
            image_url = resp.data[0].url
            revised_prompt = getattr(resp.data[0], "revised_prompt", None) or prompt
            path = _save_image_from_url(image_url, filename)

        _session_state["inline_count"] += 1

        # Clean section context for alt text
        import re
        clean_section = section_context
        clean_section = re.sub(r'\s*[\|—-]\s*(by\s+)?[^|]+\|\s*\w+[,\s]+\d{4}\s*\|.*$', '', clean_section)
        clean_section = re.sub(r'\s*[\|—-]\s*\w+[,\s]+\d{4}\s*$', '', clean_section)
        clean_section = re.sub(r'\s*[\|—-]\s*by\s+[^|]+$', '', clean_section)
        clean_section = re.sub(r'\s*[\|—-]\s*[^|]+$', '', clean_section)
        clean_section = clean_section.strip()

        return {
            "path": path,
            "url": image_url,
            "alt_text": f"A visual illustration of {clean_section}",
            "prompt_used": revised_prompt,
            "inline_index": _session_state["inline_count"],
        }
    except Exception as e:
        return {
            "path": None,
            "url": None,
            "alt_text": f"Failed to generate inline image for {section_context}",
            "error": str(e),
        }
