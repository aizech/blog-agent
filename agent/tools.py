"""Custom tools for the blog writer agent."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from agno.tools import tool
from bs4 import BeautifulSoup
from readability import Document

# --- Paths ---
OUTPUT_POSTS = Path(__file__).resolve().parent.parent / "output" / "posts"
OUTPUT_IMAGES = Path(__file__).resolve().parent.parent / "output" / "images"

OUTPUT_POSTS.mkdir(parents=True, exist_ok=True)
OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# URL Fetching
# ---------------------------------------------------------------------------

@tool
def fetch_url_content(url: str) -> str:
    """Fetch and extract readable content from a URL. Returns markdown with title and body.

    Uses readability-lxml for extraction and converts to plain markdown.
    """
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; BlogWriter/1.0)"
        })
        resp.raise_for_status()

        doc = Document(resp.text)
        title = doc.title()
        body_html = doc.summary()

        soup = BeautifulSoup(body_html, "html.parser")
        text_parts = []

        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code", "blockquote"]):
            tag = el.name
            text = el.get_text(strip=True)
            if not text:
                continue
            if tag in ("h1",):
                text_parts.append(f"# {text}")
            elif tag in ("h2",):
                text_parts.append(f"## {text}")
            elif tag in ("h3",):
                text_parts.append(f"### {text}")
            elif tag in ("h4",):
                text_parts.append(f"#### {text}")
            elif tag == "li":
                text_parts.append(f"- {text}")
            elif tag == "pre":
                code = el.get_text()
                text_parts.append(f"```\n{code}\n```")
            elif tag == "blockquote":
                text_parts.append(f"> {text}")
            else:
                text_parts.append(text)

        body = "\n\n".join(text_parts)
        return json.dumps({"title": title, "content": body, "url": url, "word_count": len(body.split())})

    except Exception as e:
        return json.dumps({"error": str(e), "url": url})


# ---------------------------------------------------------------------------
# File Saving
# ---------------------------------------------------------------------------

@tool
def save_blog_post(content: str, filename: Optional[str] = None) -> str:
    """Save blog post markdown to output/posts/. Auto-generates filename if not given.

    Args:
        content: Markdown content of the blog post.
        filename: Optional filename (without path). Default: blog-{timestamp}.md.

    Returns:
        Absolute path to the saved file.
    """
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog-{ts}.md"
    if not filename.endswith(".md"):
        filename += ".md"

    path = OUTPUT_POSTS / filename
    path.write_text(content, encoding="utf-8")
    return str(path.resolve())


@tool
def save_image(image_data: bytes, filename: str) -> str:
    """Save image bytes to output/images/.

    Args:
        image_data: Raw image bytes (PNG).
        filename: Filename for the image (e.g., 'hero.png').

    Returns:
        Absolute path to the saved file.
    """
    path = OUTPUT_IMAGES / filename
    path.write_bytes(image_data)
    return str(path.resolve())


# ---------------------------------------------------------------------------
# Outline Generation
# ---------------------------------------------------------------------------

@tool
def generate_outline(topic: str, tone_preset: str = "default", url_content: str = "") -> str:
    """Generate a blog post outline. Returns JSON with headings and key points.

    NOTE: This is a placeholder — the actual outline generation happens via
    the Agno agent in workflow.py. This tool exists so the agent can call it
    if needed, but the primary orchestration is in workflow.py.

    Args:
        topic: Blog post topic or idea.
        tone_preset: One of 'default', 'executive', 'tutorial', 'deep-dive'.
        url_content: Optional scraped content from a URL (JSON string).

    Returns:
        JSON string with outline structure.
    """
    # The real logic is in the agent call — this tool is a fallback
    return json.dumps({
        "topic": topic,
        "tone": tone_preset,
        "message": "Outline generation should be handled by the agent via workflow.py"
    })


# ---------------------------------------------------------------------------
# Social Snippet Generation
# ---------------------------------------------------------------------------

@tool
def generate_social_snippets(blog_content: str) -> str:
    """Generate social media snippets from blog post content.

    Returns JSON with tweets, LinkedIn post, and newsletter intro.

    Args:
        blog_content: Full markdown content of the blog post.

    Returns:
        JSON string with social snippets.
    """
    # This is a placeholder — actual generation happens via agent in workflow.py
    return json.dumps({
        "tweets": [],
        "linkedin": "",
        "newsletter": "",
        "message": "Social snippet generation handled by agent via workflow.py"
    })


# ---------------------------------------------------------------------------
# Format Export
# ---------------------------------------------------------------------------

def _markdown_to_html(md_content: str) -> str:
    """Simple markdown-to-HTML conversion for export."""
    import markdown as md_lib
    return md_lib.markdown(md_content, extensions=["fenced_code", "tables", "codehilite"])


@tool
def export_formats(md_content: str, formats: str = "md,html") -> str:
    """Convert blog post to multiple export formats.

    Args:
        md_content: Full markdown content.
        formats: Comma-separated list: md, html, devto, medium.

    Returns:
        JSON with each format as a key.
    """
    result = {}
    fmt_list = [f.strip().lower() for f in formats.split(",")]

    if "md" in fmt_list:
        result["md"] = md_content

    if "html" in fmt_list:
        html = _markdown_to_html(md_content)
        result["html"] = html

    if "devto" in fmt_list:
        # Dev.to: markdown with YAML frontmatter
        # Extract title from first # heading
        title_match = re.search(r"^# (.+)$", md_content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Blog Post"
        result["devto"] = f"---\ntitle: {title}\npublished: false\ntags: programming, technology\n---\n\n{md_content}"

    if "medium" in fmt_list:
        # Medium-compatible markdown (no YAML frontmatter needed)
        result["medium"] = md_content

    return json.dumps(result, indent=2)
