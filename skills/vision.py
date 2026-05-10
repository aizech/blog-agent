"""Vision analysis using OpenAI's vision-capable models.

Uses the configured vision model from config.yaml for all image analysis tasks.
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional

import requests
from PIL import Image

from config import load_config


def _get_vision_config() -> dict:
    """Load vision configuration from config.yaml."""
    cfg = load_config()
    return cfg.get("vision", {
        "model": "gpt-4o",
        "detail": "auto",
        "max_image_size": 2048,
    })


def _resize_image(image_path: str, max_size: int) -> Image.Image:
    """Resize image if larger than max_size on any dimension.

    Args:
        image_path: Path to the image file.
        max_size: Maximum dimension in pixels.

    Returns:
        PIL Image, potentially resized.
    """
    img = Image.open(image_path)
    width, height = img.size

    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    return img


def _encode_image(image_path: str, max_size: int) -> str:
    """Encode image to base64, resizing if necessary.

    Args:
        image_path: Path to the image file.
        max_size: Maximum dimension in pixels.

    Returns:
        Base64 encoded image string.
    """
    img = _resize_image(image_path, max_size)

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def analyze_image(
    image_path: str,
    prompt: str = "Describe this image in detail.",
    model: Optional[str] = None,
    detail: Optional[Literal["auto", "low", "high"]] = None,
) -> str:
    """Analyze an image using the configured vision model.

    Args:
        image_path: Path to the image file.
        prompt: The prompt/question about the image.
        model: Override the configured vision model (optional).
        detail: Override the configured detail level (optional).

    Returns:
        The model's response text.
    """
    import openai

    vision_cfg = _get_vision_config()
    model = model or vision_cfg.get("model", "gpt-4o")
    detail_level = detail or vision_cfg.get("detail", "auto")
    max_size = vision_cfg.get("max_image_size", 2048)

    # Encode image
    base64_image = _encode_image(image_path, max_size)

    # Call vision API
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": detail_level,
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content or ""


def validate_brand_alignment(
    image_path: str,
    brand_kit: dict,
    model: Optional[str] = None,
) -> dict:
    """Validate if an image aligns with brand guidelines using vision.

    Args:
        image_path: Path to the generated image.
        brand_kit: Brand configuration dict with palette, style, tone.
        model: Override the configured vision model (optional).

    Returns:
        Dict with 'score' (0-10), 'issues' (list), and 'suggestion' (str).
    """
    palette = brand_kit.get("palette", {})
    style = brand_kit.get("style", "")
    tone = brand_kit.get("tone", "")

    prompt = f"""Analyze this image for brand alignment.

Brand Guidelines:
- Style: {style}
- Tone: {tone}
- Primary Color: {palette.get('primary', 'N/A')}
- Accent Color: {palette.get('accent', 'N/A')}
- Background: {palette.get('background', 'N/A')}

Evaluate on:
1. Color palette match
2. Style consistency
3. Presence of text/watermarks (should be none)
4. Composition appropriateness

Return a JSON-like response:
{{
    "score": 0-10,
    "issues": ["issue 1", "issue 2"],
    "suggestion": "How to improve"
}}

Be critical and specific."""

    result = analyze_image(image_path, prompt, model=model)

    # Parse result - in production, use structured output
    # For now, return raw response wrapped
    return {
        "score": 7,  # Default placeholder
        "issues": [],
        "suggestion": result,
        "raw_response": result,
    }


def describe_for_recreation(
    image_path: str,
    target_type: Literal["hero", "inline"] = "inline",
    model: Optional[str] = None,
) -> str:
    """Describe an image so it can be recreated in a different style.

    Args:
        image_path: Path to the source image.
        target_type: Whether this will be a hero or inline image.
        model: Override the configured vision model (optional).

    Returns:
        A detailed description suitable for image generation prompts.
    """
    aspect_hint = "wide landscape composition, suitable as page header" if target_type == "hero" else "square composition, suitable for inline use"

    prompt = f"""Describe this image in detail so it can be recreated.

Focus on:
- Main subject matter and composition
- Colors and color relationships
- Style and artistic approach
- Mood and atmosphere
- Any text or UI elements
- Spatial arrangement

The image will be recreated with {aspect_hint}.

Provide a detailed description that captures the essence without copying the exact execution."""

    return analyze_image(image_path, prompt, model=model)
