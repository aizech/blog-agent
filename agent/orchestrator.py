"""Agno Agent factory. Creates a configured BlogWriter agent with skills + tools."""

import importlib
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.skills.agent_skills import Skills
from agno.skills.loaders.local import LocalSkills

from config import load_config

from .tools import (
    export_formats,
    fetch_url_content,
    generate_outline,
    generate_social_snippets,
    save_blog_post,
    save_image,
)

_PROVIDER_MAP: dict[str, tuple[str, str]] = {
    "openai": ("agno.models.openai", "OpenAIChat"),
    "anthropic": ("agno.models.anthropic", "Claude"),
    "groq": ("agno.models.groq", "Groq"),
    "ollama": ("agno.models.ollama", "Ollama"),
    "google": ("agno.models.google", "Gemini"),
}


def _resolve_model(provider: str, model_id: str) -> Any:
    """Dynamically import and instantiate the agno model class for the given provider.

    Args:
        provider: Provider key from config (e.g. 'openai').
        model_id: Model id string (e.g. 'gpt-4o').

    Returns:
        Instantiated agno model object.
    """
    if provider not in _PROVIDER_MAP:
        raise ValueError(
            f"Unknown provider '{provider}'. Supported: {list(_PROVIDER_MAP.keys())}"
        )
    module_path, class_name = _PROVIDER_MAP[provider]
    module = importlib.import_module(module_path)
    model_class = getattr(module, class_name)
    return model_class(id=model_id)


# Resolve skill paths relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PROJECT_ROOT / "skills"


def create_blog_agent() -> Agent:
    """Create and return a configured Agno Agent for blog writing.

    Agent has:
    - technical-blog-writer skill (via LocalSkills)
    - imagegen skill (via LocalSkills)
    - Custom tools for fetch, save, generate
    - Clear instructions to use skills before writing
    """
    cfg = load_config()
    model = _resolve_model(cfg["llm"]["provider"], cfg["llm"]["model"])

    # Load skills from local filesystem
    skill_paths = []

    tech_writer_path = SKILL_DIR / "technical-blog-writer"
    if tech_writer_path.exists():
        skill_paths.append(tech_writer_path)
    else:
        print(f"WARNING: technical-blog-writer skill not found at {tech_writer_path}")

    imagegen_path = SKILL_DIR / "imagegen"
    if imagegen_path.exists():
        skill_paths.append(imagegen_path)
    else:
        print(f"WARNING: imagegen skill not found at {imagegen_path}")

    skills = Skills(
        loaders=[LocalSkills(path=str(p)) for p in skill_paths]
    ) if skill_paths else None

    agent = Agent(
        model=model,
        name="BlogWriter",
        description=(
            "You are a technical blog writer assistant. You produce expert-level blog posts "
            "that are accessible to non-developers. You also generate hero + inline images."
        ),
        instructions=[
            "You have access to skills that provide specialized writing and image generation instructions.",
            "",
            "BEFORE writing, call get_skill_instructions('technical-blog-writer') to load blog guidelines.",
            "Before generating images, call get_skill_instructions('imagegen') for image guidelines.",
            "",
            "Follow the technical-blog-writer skill guidelines carefully:",
            "- Use problem-solution structure",
            "- Write in team voice (we/our) — Anthropic-like, conversational-expert",
            "- Include FAQ section (3-5 questions)",
            "- Include code examples only when they add clarity",
            "- Cite sources inline with [source: URL]",
            "",
            "For images:",
            "- Hero image is always required",
            "- Inline images are optional, max 2 per post",
            "- All images must share a consistent visual style",
            "",
            "Output in markdown.",
        ],
        tools=[
            fetch_url_content,
            save_blog_post,
            generate_outline,
            generate_social_snippets,
            export_formats,
            save_image,
        ],
        skills=skills,
        markdown=True,
    )

    return agent
