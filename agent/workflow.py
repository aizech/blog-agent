"""Workflow orchestrator. Manages sequential steps of blog generation.

Steps:
1. outline  — generate outline from topic/URL
2. draft   — write full blog post from outline
3. images  — generate hero + optional inline images
4. social  — generate social media snippets
5. export  — format conversion
"""

import json
import re
from typing import Generator, Optional

from agno.agent import Agent

from agent.tools import export_formats
from config import load_active_brand, load_brand, load_config
from skills.image_gen import (
    generate_hero_image,
    generate_inline_image,
    reset_session as reset_image_session,
)


class BlogWorkflow:
    """Orchestrates the multi-step blog generation workflow.

    Each step calls the Agno agent with specific context + instructions.
    """

    def __init__(self, agent: Agent):
        self.agent = agent
        self._output = {
            "outline": None,
            "draft": None,
            "hero_variants": [],
            "hero_chosen": None,
            "inline_images": [],
            "social_snippets": None,
            "exports": None,
        }

    # ------------------------------------------------------------------
    # Step 1: Outline
    # ------------------------------------------------------------------

    def generate_outline(
        self,
        topic: str,
        tone_preset: str = "default",
        url_content: Optional[str] = None,
    ) -> str:
        """Generate blog outline. Returns markdown outline string.

        Args:
            topic: Blog topic or idea.
            tone_preset: 'default', 'executive', 'tutorial', 'deep-dive'.
            url_content: Optional fetched URL content (JSON string).
        """
        tone_desc = {
            "default": "Team voice — we/our, conversational-expert, problem-solution structure.",
            "executive": "Short paragraphs, decision-focused, minimal code, executive tone.",
            "tutorial": "Step-by-step, more code examples, beginner-friendly explanations.",
            "deep-dive": "Longer sections, theory, academic references, deep technical detail.",
        }.get(tone_preset, "Team voice — we/our, conversational-expert.")

        msg_parts = [
            "## Task: Generate Blog Outline",
            f"Topic: {topic}",
            f"Tone preset: {tone_preset}",
            f"Tone description: {tone_desc}",
        ]

        if url_content:
            try:
                data = json.loads(url_content)
                if "error" not in data:
                    msg_parts.append(f"Source URL: {data.get('url', 'unknown')}")
                    msg_parts.append(f"Source title: {data.get('title', 'unknown')}")
                    msg_parts.append(f"Source content preview:\n\n{data.get('content', '')[:3000]}")
            except (json.JSONDecodeError, KeyError):
                pass

        msg_parts.append(
            "\n\nGenerate a detailed outline with sections and key points per section. "
            "Output ONLY the outline in markdown. "
            "Get skill instructions first: call get_skill_instructions('technical-blog-writer') "
            "before writing."
        )

        message = "\n\n".join(msg_parts)
        response = self.agent.run(message)
        outline = response.content if hasattr(response, "content") else str(response)
        self._output["outline"] = outline
        return outline

    # ------------------------------------------------------------------
    # Step 2: Full Draft
    # ------------------------------------------------------------------

    def write_draft(
        self,
        topic: str,
        outline: str,
        tone_preset: str = "default",
        url_content: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Write full blog post from outline. Streams markdown tokens.

        Accumulates full text in self._output['draft'].

        Yields:
            Chunks of markdown content as they arrive.
        """
        tone_desc = {
            "default": "Team voice — we/our, conversational-expert.",
            "executive": "Executive tone — short, decision-focused.",
            "tutorial": "Tutorial — step-by-step, more code.",
            "deep-dive": "Deep-dive — longer sections, theory.",
        }.get(tone_preset, "Team voice — we/our, conversational-expert.")

        msg_parts = [
            "## Task: Write Full Blog Post",
            f"Topic: {topic}",
            f"Tone: {tone_desc}",
            "",
            "## Approved Outline",
            outline,
        ]

        if url_content:
            try:
                data = json.loads(url_content)
                if "error" not in data:
                    msg_parts.append(f"## Source Material\n\n{data.get('content', '')[:5000]}")
            except (json.JSONDecodeError, KeyError):
                pass

        msg_parts.append(
            "\n\nWrite the full blog post following the outline exactly. "
            "Requirements:"
            "\n- Call get_skill_instructions('technical-blog-writer') first."
            "\n- Use problem-solution structure."
            "\n- Team voice (we/our)."
            "\n- Include TL;DR, FAQ section (3-5 questions), and code examples where helpful."
            "\n- Annotate claims with [source: URL] inline."
            "\n- Add a 'Sources' section at the bottom with all referenced URLs."
            "\n- At the very end, add a section '<!-- inline-image-opportunities -->' listing "
            "each section that would benefit from an inline image. One line per opportunity, "
            "format: `SECTION: <heading> — DESCRIPTION: <what to illustrate>`."
            "\n- Output full markdown."
        )

        message = "\n\n".join(msg_parts)
        # Stream the response and accumulate
        full_text = ""
        for chunk in self.agent.run(message, stream=True):
            content = chunk.content if hasattr(chunk, "content") else None
            if content and isinstance(content, str):
                full_text += content
                yield content

        self._output["draft"] = full_text

    # ------------------------------------------------------------------
    # Step 3: Images
    # ------------------------------------------------------------------

    def generate_hero_images(
        self,
        topic: str,
        tone_preset: str = "default",
        brand_name: Optional[str] = None,
        session_timestamp: Optional[str] = None,
    ) -> list:
        """Generate hero image variants (count from config).

        Args:
            topic: Blog post topic.
            tone_preset: Tone preset key.
            brand_name: Brand name to load (uses active brand if None).
            session_timestamp: Optional timestamp for consistent filenames.

        Returns:
            List of variant dicts with path, url, alt_text.
        """
        num_variants = load_config()["image"]["hero"]["num_variants"]
        brand_kit = load_brand(brand_name) if brand_name else load_active_brand()
        reset_image_session()
        result = generate_hero_image(topic, tone_preset, num_variants=num_variants, brand_kit=brand_kit, session_timestamp=session_timestamp)
        variants = result.get("variants", [])
        self._output["hero_variants"] = variants
        return variants

    def select_hero(self, variant_index: int):
        """User selects which hero variant to keep."""
        variants = self._output.get("hero_variants", [])
        if 0 <= variant_index < len(variants):
            self._output["hero_chosen"] = variants[variant_index]

    def generate_inline_images(
        self,
        topic: str,
        draft: str,
        brand_name: Optional[str] = None,
        session_timestamp: Optional[str] = None,
    ) -> list:
        """Parse inline-image-opportunities from draft and generate up to 2 inline images.

        Args:
            topic: Blog post topic.
            draft: Full markdown draft (contains <!-- inline-image-opportunities --> section).
            brand_name: Brand name to load (uses active brand if None).
            session_timestamp: Optional timestamp for consistent filenames.

        Returns:
            List of generated inline image dicts.
        """
        brand_kit = load_brand(brand_name) if brand_name else load_active_brand()
        images = []
        opportunities = self._parse_inline_opportunities(draft)

        for opp in opportunities[:2]:  # max 2
            result = generate_inline_image(topic, opp["description"], brand_kit=brand_kit, session_timestamp=session_timestamp)
            if result.get("error") == "INLINE_CAP_REACHED":
                break
            if result.get("path"):
                result["section"] = opp["section"]
                images.append(result)

        self._output["inline_images"] = images
        return images

    def _parse_inline_opportunities(self, draft: str) -> list:
        """Extract inline image opportunities from the draft marker section."""
        opportunities = []
        in_marker = False
        for line in draft.split("\n"):
            if "<!-- inline-image-opportunities -->" in line:
                in_marker = True
                continue
            if in_marker:
                line = line.strip()
                if not line or line.startswith("```"):
                    continue
                m = re.match(r"SECTION:\s*(.+?)\s*—\s*DESCRIPTION:\s*(.+)", line)
                if m:
                    opportunities.append({
                        "section": m.group(1).strip(),
                        "description": m.group(2).strip(),
                    })
        return opportunities

    # ------------------------------------------------------------------
    # Step 4: Social Snippets
    # ------------------------------------------------------------------

    def generate_social_snippets(self, draft: str) -> dict:
        """Generate social media snippets from the draft.

        Returns:
            Dict with 'tweets', 'linkedin', 'newsletter' keys.
        """
        msg = (
            "## Task: Generate Social Media Snippets\n\n"
            "From the blog post below, generate:\n"
            "1. A thread of 3 tweets (Twitter/X style, each under 280 chars)\n"
            "2. A LinkedIn post (2-3 paragraphs, professional)\n"
            "3. A newsletter intro paragraph (1 paragraph, hook-driven)\n\n"
            "IMPORTANT: Respond with ONLY a raw JSON object. No explanation, no markdown fences, "
            "no prose before or after. The JSON must have exactly these keys: "
            "tweets (list of 3 strings), linkedin (string), newsletter (string).\n\n"
            f"## Blog Post\n\n{draft[:4000]}"
        )
        response = self.agent.run(msg)
        content = response.content if hasattr(response, "content") else str(response)
        try:
            snippets = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    snippets = json.loads(match.group())
                except (json.JSONDecodeError, TypeError):
                    snippets = {"tweets": [], "linkedin": content, "newsletter": ""}
            else:
                snippets = {"tweets": [], "linkedin": content, "newsletter": ""}
        self._output["social_snippets"] = snippets
        return snippets

    # ------------------------------------------------------------------
    # Step 5: Export
    # ------------------------------------------------------------------

    def export_post(self, draft: str, formats: str = "md,html") -> dict:
        """Convert draft to export formats.

        Args:
            draft: Markdown content.
            formats: Comma-separated format list.

        Returns:
            Dict with format keys.
        """
        # entrypoint is the raw function wrapped by @tool decorator
        result = export_formats.entrypoint(draft, formats)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                result = {"md": draft}
        self._output["exports"] = result
        return result

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def output(self) -> dict:
        return self._output

    @property
    def draft(self) -> Optional[str]:
        return self._output.get("draft")
