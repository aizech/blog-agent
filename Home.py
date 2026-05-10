"""Blog Writer Agent — Streamlit frontend."""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml
from streamlit_ace import st_ace

from agent.orchestrator import create_blog_agent
from agent.tools import fetch_url_content, save_blog_post
from agent.workflow import BlogWorkflow
from config import list_brands, load_config

# ---- Output Paths ----
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
POSTS_DIR = OUTPUT_DIR / "posts"
IMAGES_DIR = OUTPUT_DIR / "images"
PROMPTS_DIR = OUTPUT_DIR / "prompts"

for d in [POSTS_DIR, IMAGES_DIR, PROMPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def save_generation_prompts(session_timestamp: str, hero_variants: list, inline_images: list):
    """Save image generation prompts to YAML file.

    Args:
        session_timestamp: Session identifier (e.g., "20250110_143022")
        hero_variants: List of hero image variant dicts with 'prompt_used'
        inline_images: List of inline image dicts with 'prompt_used'
    """
    prompts = {
        "session_timestamp": session_timestamp,
        "generated_at": datetime.now().isoformat(),
        "hero_images": [],
        "inline_images": [],
    }

    for i, var in enumerate(hero_variants):
        if var.get("prompt_used"):
            prompts["hero_images"].append({
                "variant": i + 1,
                "prompt": var["prompt_used"],
                "alt_text": var.get("alt_text", ""),
                "path": var.get("path", ""),
            })

    for i, img in enumerate(inline_images):
        if img.get("prompt_used"):
            prompts["inline_images"].append({
                "index": i + 1,
                "section": img.get("section", ""),
                "prompt": img["prompt_used"],
                "alt_text": img.get("alt_text", ""),
                "path": img.get("path", ""),
            })

    filename = f"prompts-{session_timestamp}.yaml"
    path = PROMPTS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(prompts, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return str(path)


def strip_markdown_fences(text: str) -> str:
    """Strip markdown code fence markers that wrap the entire content.

    LLMs sometimes wrap output in ```markdown ... ``` fences.
    This function removes those outer fences when present.

    Args:
        text: Raw markdown text that may be wrapped in fences

    Returns:
        Clean markdown text without outer fences
    """
    text = text.strip()

    # Check for ```markdown or ``` at the start
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()

    # Check for ``` at the end
    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def auto_save_draft(session_timestamp: str, draft: str):
    """Auto-save draft to output/posts/ after generation.

    Args:
        session_timestamp: Session identifier
        draft: Markdown content

    Returns:
        Path to saved file
    """
    # Clean the draft from markdown code fences
    clean_draft = strip_markdown_fences(draft)

    filename = f"blog-{session_timestamp}-auto.md"
    path = POSTS_DIR / filename
    path.write_text(clean_draft, encoding="utf-8")
    return str(path)

# ---- Page config ----
st.set_page_config(
    page_title="Blog Writer Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Constants ----
TONE_OPTIONS = {
    "default": "Default — team voice, conversational-expert",
    "executive": "Executive — short, decision-focused, minimal code",
    "tutorial": "Tutorial — step-by-step, beginner-friendly, more code",
    "deep-dive": "Deep Dive — longer sections, theory, academic depth",
}
INPUT_MODE_URL = "Rewrite from URL"
INPUT_MODE_IDEA = "Write from idea"


# ---- Session State ----
def init_session():
    """Initialize all session state variables."""
    defaults = {
        "step": "IDLE",
        "agent": None,
        "workflow": None,
        "input_mode": INPUT_MODE_IDEA,
        "topic": "",
        "url_input": "",
        "url_content": None,
        "tone_preset": "default",
        "outline": None,
        "outline_approved": False,
        "draft": None,
        "draft_raw": None,
        "hero_variants": [],
        "hero_chosen_idx": None,
        "inline_images": [],
        "social_snippets": None,
        "exports": None,
        "history": [],
        "cost": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "images": 0},
        "brand": load_config().get("active_brand", ""),
        "error": None,
        "processing": False,
        "session_timestamp": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ---- Initialize Agent (once) ----
if st.session_state.agent is None:
    with st.spinner("Loading agent and skills..."):
        agent = create_blog_agent()
        st.session_state.agent = agent
        st.session_state.workflow = BlogWorkflow(agent)


# ================================================================
# SIDEBAR
# ================================================================

with st.sidebar:
    st.markdown("## ✍️ Blog Writer Agent")
    st.caption("technical-blog-writer skill • hero and inline images")
    st.divider()

    # ---- Session History ----
    st.markdown("### 📋 Session History")
    if st.session_state.history:
        for i, entry in enumerate(st.session_state.history):
            label = f"{entry['topic'][:40]}..." if len(entry['topic']) > 40 else entry['topic']
            if st.button(f"{i+1}. {label}", key=f"hist_{i}", width='stretch'):
                st.session_state.draft = entry["draft"]
                st.session_state.hero_variants = entry.get("hero_variants", [])
                st.session_state.hero_chosen_idx = entry.get("hero_chosen_idx")
                st.session_state.inline_images = entry.get("inline_images", [])
                st.session_state.step = "EXPORT"
                st.rerun()
    else:
        st.caption("No posts generated yet.")

    st.divider()

    # ---- Cost Tracker ----
    c = st.session_state.cost
    total_tokens = c["prompt_tokens"] + c["completion_tokens"]
    est_cost = (c["prompt_tokens"] / 1_000_000 * 2.50 +
                c["completion_tokens"] / 1_000_000 * 10.00 +
                c["images"] * 0.08)  # DALL-E 3 HD ~$0.08/image
    st.markdown("### 💰 Session Cost")
    st.caption(f"LLM calls: {c['calls']}")
    st.caption(f"Tokens: {total_tokens:,} (${est_cost:.4f})")
    st.caption(f"Images: {c['images']} (${c['images'] * 0.08:.2f})")
    st.caption(f"**Total: ${est_cost:.4f}**")

    st.divider()

    # ---- New Post Button ----
    if st.button("🆕 New Post", width='stretch', type="primary"):
        for k in ["step", "topic", "url_input", "url_content", "outline",
                   "outline_approved", "draft", "draft_raw", "hero_variants",
                   "hero_chosen_idx", "inline_images", "social_snippets",
                   "exports", "error", "processing"]:
            if k in st.session_state:
                if k in ("step",):
                    st.session_state[k] = "IDLE"
                elif k in ("processing", "outline_approved"):
                    st.session_state[k] = False
                else:
                    st.session_state[k] = None if k != "hero_variants" else []
        st.rerun()


# ================================================================
# MAIN CONTENT
# ================================================================

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("# ✍️ Blog Writer Agent")
    st.markdown("Generate technical blog posts from an idea or URL. "
                "Uses the **technical-blog-writer** skill for team-voice content "
                "and creates hero + inline images with brand style.")

with col2:
    if st.session_state.error:
        st.error(st.session_state.error)
        st.session_state.error = None


# ---- Step: IDLE (Input Form) ----
if st.session_state.step == "IDLE":
    st.divider()

    input_mode = st.radio(
        "Input type",
        [INPUT_MODE_IDEA, INPUT_MODE_URL],
        horizontal=True,
        index=0 if st.session_state.input_mode == INPUT_MODE_IDEA else 1,
        key="input_mode_radio",
    )
    st.session_state.input_mode = input_mode

    tone = st.selectbox(
        "Tone preset",
        options=list(TONE_OPTIONS.keys()),
        format_func=lambda k: TONE_OPTIONS[k],
        key="tone_select",
    )
    st.session_state.tone_preset = tone

    _brands = list_brands()
    _brand_default = st.session_state.brand if st.session_state.brand in _brands else (_brands[0] if _brands else "")
    if _brands:
        selected_brand = st.selectbox(
            "Brand",
            options=_brands,
            index=_brands.index(_brand_default),
            key="brand_select",
            help="Visual brand style applied to all generated images",
        )
        st.session_state.brand = selected_brand

    if input_mode == INPUT_MODE_IDEA:
        topic = st.text_area(
            "What's your blog post idea?",
            placeholder="e.g., Database indexing explained for junior developers",
            height=120,
            key="idea_input",
        )
        st.session_state.topic = topic
        st.session_state.url_input = ""
    else:
        url = st.text_input(
            "URL to rewrite",
            placeholder="https://example.com/blog-post",
            key="url_input_field",
        )
        st.session_state.url_input = url
        st.session_state.topic = ""

    col_a, col_b = st.columns([1, 3])
    with col_a:
        generate_btn = st.button(
            "🚀 Generate",
            type="primary",
            width='stretch',
            disabled=st.session_state.processing
            or (input_mode == INPUT_MODE_IDEA and not st.session_state.topic)
            or (input_mode == INPUT_MODE_URL and not st.session_state.url_input),
        )

    if generate_btn and not st.session_state.processing:
        from datetime import datetime
        st.session_state.processing = True
        st.session_state.step = "FETCHING"
        st.session_state.outline_approved = False
        st.session_state.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.rerun()

# ---- Step: FETCHING (URL extraction) ----
elif st.session_state.step == "FETCHING":
    st.divider()
    with st.status("🔍 Fetching URL content...", expanded=True) as status:
        url = st.session_state.url_input
        result_str = fetch_url_content.entrypoint(url)
        try:
            result = json.loads(result_str)
        except json.JSONDecodeError:
            result = {"error": "Failed to parse response", "content": result_str}

        if "error" in result:
            st.error(f"Failed to fetch URL: {result['error']}")
            st.session_state.error = result["error"]
            st.session_state.step = "IDLE"
            st.session_state.processing = False
            st.stop()
        else:
            st.success(f"Fetched: {result.get('title', 'Untitled')}")
            st.caption(f"~{result.get('word_count', 0)} words extracted")
            st.session_state.url_content = result_str
            st.session_state.topic = result.get("title", "Untitled")
            status.update(label="✅ URL fetched", state="complete")

    st.session_state.step = "OUTLINING"
    time.sleep(0.5)
    st.rerun()

# ---- Step: OUTLINING (Generate + Show Outline) ----
elif st.session_state.step == "OUTLINING":
    st.divider()
    st.markdown("### 📝 Generating Outline...")
    progress_text = "Analyzing topic and generating structure..."
    progress_bar = st.progress(0, text=progress_text)

    workflow: BlogWorkflow = st.session_state.workflow
    topic = st.session_state.topic
    tone = st.session_state.tone_preset
    url_content = st.session_state.url_content

    try:
        outline = workflow.generate_outline(topic, tone, url_content)
        st.session_state.outline = outline
        st.session_state.step = "APPROVE"
        progress_bar.progress(100, text="✅ Outline generated")
    except Exception as e:
        st.error(f"Failed to generate outline: {e}")
        st.session_state.error = str(e)
        st.session_state.step = "IDLE"
        st.session_state.processing = False
        st.stop()

    time.sleep(0.3)
    st.rerun()

# ---- Step: APPROVE (Review + Edit Outline) ----
elif st.session_state.step == "APPROVE":
    st.divider()
    st.markdown("### 📋 Outline Review")
    st.markdown("Review the outline below. You can edit it before generating the full draft.")

    edited_outline = st.text_area(
        "Edit outline as needed:",
        value=st.session_state.outline,
        height=400,
        key="outline_editor",
    )

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        if st.button("✅ Approve & Write Draft", type="primary", width='stretch'):
            st.session_state.outline = edited_outline
            st.session_state.outline_approved = True
            st.session_state.step = "WRITING"
            st.rerun()
    with col_b:
        if st.button("🔄 Regenerate Outline", width='stretch'):
            st.session_state.step = "OUTLINING"
            st.rerun()
    with col_c:
        if st.button("⬅️ Back to Start", width='stretch'):
            st.session_state.step = "IDLE"
            st.session_state.processing = False
            st.rerun()

# ---- Step: WRITING (Stream Full Draft) ----
elif st.session_state.step == "WRITING":
    st.divider()
    st.markdown("### ✍️ Writing Blog Post...")

    workflow: BlogWorkflow = st.session_state.workflow
    topic = st.session_state.topic
    tone = st.session_state.tone_preset
    outline = st.session_state.outline
    url_content = st.session_state.url_content

    # Progress narrative
    progress_placeholder = st.empty()
    progress_placeholder.info("📝 Drafting content...")

    # Stream the draft
    with st.container():
        stream = workflow.write_draft(topic, outline, tone, url_content)
        draft = st.write_stream(stream)

    st.session_state.draft = draft
    st.session_state.draft_raw = workflow.draft

    # Auto-save draft to output folder
    if st.session_state.session_timestamp and draft:
        auto_path = auto_save_draft(st.session_state.session_timestamp, draft)
        st.session_state.auto_saved_path = auto_path

    # Track tokens from last agent call
    # (agent run metrics are in the last chunk's metrics)
    progress_placeholder.success("✅ Blog post written!")

    st.session_state.step = "EDIT_DRAFT"
    st.rerun()

# ---- Step: EDIT_DRAFT (Markdown Editor) ----
elif st.session_state.step == "EDIT_DRAFT":
    st.divider()
    st.markdown("### 📝 Edit Blog Post")
    st.caption("Review and edit the draft in the markdown editor below. Changes are saved when you continue.")

    # Show the ace editor with current draft
    edited_draft = st_ace(
        value=st.session_state.draft or "",
        language="markdown",
        theme="textmate",
        key="ace_editor",
        height=600,
        wrap=True,
        auto_update=True,
        show_gutter=True,
        show_print_margin=False,
    )

    # Buttons
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        if st.button("💾 Save & Generate Hero Images", type="primary", width='stretch'):
            st.session_state.draft = edited_draft
            st.session_state.step = "IMAGES_HERO"
            st.rerun()
    with col_b:
        if st.button("⬅️ Back to Outline", width='stretch'):
            st.session_state.step = "APPROVE"
            st.rerun()
    with col_c:
        if st.button("🔄 Regenerate Draft", width='stretch'):
            st.session_state.step = "WRITING"
            st.rerun()

# ---- Step: IMAGES_HERO (Manual Hero Generation) ----
elif st.session_state.step == "IMAGES_HERO":
    st.divider()
    st.markdown("### 🎨 Hero Images")

    workflow: BlogWorkflow = st.session_state.workflow
    topic = st.session_state.topic
    tone = st.session_state.tone_preset

    # Manual button to generate hero images
    if not st.session_state.hero_variants:
        st.info("Click below to generate hero image variants for your blog post.")
        if st.button("🎨 Generate Hero Images", type="primary", width='stretch'):
            with st.status("🎨 Generating hero image variants...", expanded=True) as status:
                try:
                    variants = workflow.generate_hero_images(topic, tone, brand_name=st.session_state.brand or None, session_timestamp=st.session_state.session_timestamp)
                    st.session_state.hero_variants = variants
                    st.session_state.cost["images"] += len([v for v in variants if v.get("path")])
                    # Save prompts to file
                    if st.session_state.session_timestamp:
                        save_generation_prompts(
                            st.session_state.session_timestamp,
                            variants,
                            st.session_state.inline_images or []
                        )
                    status.update(label=f"✅ Generated {len(variants)} hero variants", state="complete")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hero image generation failed: {e}")
                    st.session_state.hero_variants = []
    else:
        st.success(f"✅ {len(st.session_state.hero_variants)} hero variants generated")

    # Show hero variants for selection
    if st.session_state.hero_variants:
        st.markdown("#### Select Hero Image")

        variants = st.session_state.hero_variants
        chosen = st.session_state.hero_chosen_idx

        cols = st.columns(len(variants))
        for i, (col, var) in enumerate(zip(cols, variants)):
            with col:
                if var.get("path"):
                    st.image(var["path"], caption=f"Variant {i+1}", width='stretch')
                else:
                    st.warning(f"Variant {i+1} failed")
                    if var.get("error"):
                        st.caption(var["error"])

                selected = chosen == i
                if st.button(
                    f"{'✅ Selected' if selected else 'Select'} Variant {i+1}",
                    key=f"hero_sel_{i}",
                    width='stretch',
                    type="primary" if selected else "secondary",
                    disabled=selected,
                ):
                    st.session_state.hero_chosen_idx = i
                    workflow.select_hero(i)
                    st.rerun()

    # Continue button after hero selection
    if st.session_state.hero_chosen_idx is not None:
        st.divider()
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("🖼️ Generate Inline Images →", type="primary", width='stretch'):
                st.session_state.step = "IMAGES_INLINE"
                st.rerun()
        with col_b:
            if st.button("⬅️ Back to Editor", width='stretch'):
                st.session_state.step = "EDIT_DRAFT"
                st.rerun()
    else:
        if st.session_state.hero_variants:
            st.info("👆 Select a hero variant to continue.")

# ---- Step: IMAGES_INLINE (Manual Inline Generation) ----
elif st.session_state.step == "IMAGES_INLINE":
    st.divider()
    st.markdown("### 🖼️ Inline Images")

    workflow: BlogWorkflow = st.session_state.workflow
    topic = st.session_state.topic
    draft = st.session_state.draft

    # Manual button to generate inline images
    if not st.session_state.inline_images:
        st.info("Click below to generate inline images for your blog post sections.")
        if st.button("🖼️ Generate Inline Images", type="primary", width='stretch'):
            with st.status("🖼️ Generating inline images...", expanded=True) as status:
                try:
                    inline_imgs = workflow.generate_inline_images(topic, draft, brand_name=st.session_state.brand or None, session_timestamp=st.session_state.session_timestamp)
                    st.session_state.inline_images = inline_imgs
                    st.session_state.cost["images"] += len(inline_imgs)
                    # Save prompts to file (updating with inline images)
                    if st.session_state.session_timestamp:
                        save_generation_prompts(
                            st.session_state.session_timestamp,
                            st.session_state.hero_variants or [],
                            inline_imgs
                        )
                    if inline_imgs:
                        status.update(label=f"✅ Generated {len(inline_imgs)} inline images", state="complete")
                    else:
                        status.update(label="No inline images needed", state="complete")
                    st.rerun()
                except Exception as e:
                    st.caption(f"Inline image generation skipped: {e}")
                    st.session_state.inline_images = []
    else:
        st.success(f"✅ {len(st.session_state.inline_images)} inline images generated")

    # Show inline images
    if st.session_state.inline_images:
        st.markdown("#### Generated Inline Images")
        cols = st.columns(len(st.session_state.inline_images))
        for i, (col, img) in enumerate(zip(cols, st.session_state.inline_images)):
            with col:
                if img.get("path"):
                    st.image(img["path"], caption=f"Inline {i+1}: {img.get('section', '')}",
                             width='stretch')
                elif img.get("error"):
                    st.warning(f"Inline {i+1} failed: {img.get('error', 'Unknown error')[:50]}")
                else:
                    st.info(f"Inline {i+1}: No image generated")

    # Proceed or regenerate
    st.divider()
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        if st.button("✅ Continue to Export", type="primary", width='stretch'):
            st.session_state.step = "EXPORT"
            st.rerun()
    with col_b:
        if st.button("🔄 Regenerate Inline", width='stretch'):
            st.session_state.inline_images = []
            st.rerun()
    with col_c:
        if st.button("⬅️ Back to Hero Selection", width='stretch'):
            st.session_state.step = "IMAGES_HERO"
            st.rerun()

elif st.session_state.step == "EXPORT":
    # ---- Step: EXPORT (Final view with downloads + social) ----
    st.divider()
    st.markdown("## ✅ Blog Post Complete")
    st.balloons()

    # Generate social snippets if not done
    workflow = st.session_state.workflow
    if st.session_state.social_snippets is None and st.session_state.draft:
        with st.spinner("Generating social snippets..."):
            try:
                snippets = workflow.generate_social_snippets(st.session_state.draft)
                st.session_state.social_snippets = snippets
            except Exception as e:
                st.session_state.social_snippets = {"tweets": [], "linkedin": "", "newsletter": ""}

    # Generate exports if not done
    if st.session_state.exports is None and st.session_state.draft:
        with st.spinner("Converting formats..."):
            try:
                clean_draft = strip_markdown_fences(st.session_state.draft)
                exports = workflow.export_post(clean_draft, "md,html,devto,medium")
                st.session_state.exports = exports
            except Exception as e:
                st.session_state.exports = {"md": strip_markdown_fences(st.session_state.draft)}

    tab_draft, tab_images, tab_export, tab_social, tab_sources = st.tabs(
        ["📝 Draft", "🖼️ Images", "📦 Export", "📱 Social", "🔗 Sources"]
    )

    # ---- Tab: Draft ----
    with tab_draft:
        if st.session_state.draft:
            st.markdown(st.session_state.draft)
        else:
            st.warning("No draft available.")

    # ---- Tab: Images ----
    with tab_images:
        # Hero
        chosen_idx = st.session_state.hero_chosen_idx
        variants = st.session_state.hero_variants
        if chosen_idx is not None and chosen_idx < len(variants):
            var = variants[chosen_idx]
            if var.get("path"):
                st.markdown("#### Hero Image")
                st.image(var["path"], width='stretch')
                st.code(f"Alt: {var.get('alt_text', '')}")
                st.caption(f"Prompt: {var.get('prompt_used', 'N/A')}")

        # Inline
        if st.session_state.inline_images:
            st.markdown("#### Inline Images")
            for img in st.session_state.inline_images:
                if img.get("path"):
                    st.image(img["path"], caption=img.get("section", ""),
                             width='stretch')
                    st.code(f"Alt: {img.get('alt_text', '')}")

    # ---- Tab: Export ----
    with tab_export:
        exports = st.session_state.exports or {}
        st.markdown("#### Download Formats")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            if exports.get("md"):
                st.download_button(
                    "📄 Download .md",
                    data=exports["md"],
                    file_name="blog-post.md",
                    mime="text/markdown",
                    width='stretch',
                )
        with col_b:
            if exports.get("html"):
                # Wrap in HTML template
                hero_path = None
                if st.session_state.hero_chosen_idx is not None:
                    variants = st.session_state.hero_variants
                    if st.session_state.hero_chosen_idx < len(variants):
                        var = variants[st.session_state.hero_chosen_idx]
                        if var.get("path"):
                            # Read image as base64 for embedding
                            import base64
                            img_bytes = Path(var["path"]).read_bytes()
                            b64 = base64.b64encode(img_bytes).decode()
                            hero_path = f"data:image/png;base64,{b64}"

                html_template = Path(__file__).parent / "templates" / "html.html"
                if html_template.exists():
                    html_content = html_template.read_text()
                    html_content = html_content.replace("{{TITLE}}", st.session_state.topic)
                    hero_html = ""
                    if hero_path:
                        hero_html = f'<img src="{hero_path}" class="hero" alt="Hero image">'
                    html_content = html_content.replace("{{HERO_HTML}}", hero_html)
                    html_content = html_content.replace("{{CONTENT}}", exports["html"])
                else:
                    html_content = exports["html"]

                st.download_button(
                    "🌐 Download .html",
                    data=html_content,
                    file_name="blog-post.html",
                    mime="text/html",
                    width='stretch',
                )
        with col_c:
            if exports.get("devto"):
                st.download_button(
                    "📝 Download Dev.to",
                    data=exports["devto"],
                    file_name="blog-post-devto.md",
                    mime="text/markdown",
                    width='stretch',
                )
        with col_d:
            if exports.get("medium"):
                st.download_button(
                    "✍️ Download Medium",
                    data=exports["medium"],
                    file_name="blog-post-medium.md",
                    mime="text/markdown",
                    width='stretch',
                )

        # Save to disk with images embedded
        if st.button("💾 Save to output/posts/", width='stretch'):
            ts = st.session_state.session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")

            # Prepare markdown with embedded images
            content = strip_markdown_fences(st.session_state.draft) or ""

            # Add hero image at the top if available
            chosen_idx = st.session_state.hero_chosen_idx
            if chosen_idx is not None and st.session_state.hero_variants:
                hero = st.session_state.hero_variants[chosen_idx]
                if hero and hero.get("path"):
                    # Convert absolute path to relative path for markdown
                    hero_rel = hero["path"].replace("\\", "/")
                    if "output/images/" in hero_rel:
                        hero_rel = "../images/" + hero_rel.split("output/images/")[-1]
                    hero_alt = hero.get("alt_text", "Hero image")
                    hero_md = f"![{hero_alt}]({hero_rel})\n\n"
                    content = hero_md + content

            # Add inline images at their markers if available
            for img in st.session_state.inline_images:
                if img.get("path") and img.get("section"):
                    img_rel = img["path"].replace("\\", "/")
                    if "output/images/" in img_rel:
                        img_rel = "../images/" + img_rel.split("output/images/")[-1]
                    img_alt = img.get("alt_text", f"Illustration of {img['section']}")
                    img_md = f"\n![{img_alt}]({img_rel})\n"
                    # Try to insert after the section heading
                    section_pattern = f"## {img['section']}"
                    if section_pattern in content:
                        content = content.replace(section_pattern, section_pattern + img_md, 1)

            filename = f"blog-{ts}.md"
            path = save_blog_post.entrypoint(content, filename)
            st.success(f"✅ Saved to {path} with {len(st.session_state.inline_images) + (1 if chosen_idx is not None else 0)} images embedded")

    # ---- Tab: Social ----
    with tab_social:
        snippets = st.session_state.social_snippets or {}
        st.markdown("#### Twitter/X Thread")
        for i, tweet in enumerate(snippets.get("tweets", [])):
            st.text_area(f"Tweet {i+1}", value=tweet, height=80, key=f"tweet_{i}")

        st.markdown("#### LinkedIn Post")
        linkedin = snippets.get("linkedin", "")
        st.text_area("LinkedIn", value=linkedin, height=150, key="linkedin_area")

        st.markdown("#### Newsletter Intro")
        newsletter = snippets.get("newsletter", "")
        st.text_area("Newsletter", value=newsletter, height=100, key="newsletter_area")

        # Combined download
        social_text = (
            f"TWITTER THREAD:\n\n"
            + "\n\n".join(f"{i+1}. {t}" for i, t in enumerate(snippets.get("tweets", [])))
            + f"\n\nLINKEDIN:\n\n{linkedin}"
            + f"\n\nNEWSLETTER:\n\n{newsletter}"
        )
        st.download_button(
            "📱 Download All Snippets",
            data=social_text,
            file_name="social-snippets.txt",
            mime="text/plain",
        )

    # ---- Tab: Sources ----
    with tab_sources:
        st.markdown("#### Sources Referenced")
        if st.session_state.url_input:
            st.markdown(f"- **Source URL**: [{st.session_state.url_input}]({st.session_state.url_input})")
        if st.session_state.url_content:
            try:
                data = json.loads(st.session_state.url_content)
                if data.get("title"):
                    st.markdown(f"- **Title**: {data['title']}")
            except (json.JSONDecodeError, KeyError):
                pass
        st.caption("Inline citations are marked with [source: URL] in the draft above.")

    # ---- Save to history ----
    if st.session_state.draft and (
        not st.session_state.history
        or st.session_state.history[-1].get("draft") != st.session_state.draft
    ):
        st.session_state.history.append({
            "topic": st.session_state.topic,
            "draft": st.session_state.draft,
            "hero_variants": st.session_state.hero_variants,
            "hero_chosen_idx": st.session_state.hero_chosen_idx,
            "inline_images": st.session_state.inline_images,
            "timestamp": time.time(),
        })

    # ---- Regenerate ----
    st.divider()
    col_a, col_b = st.columns([1, 5])
    with col_a:
        if st.button("🔄 Start New Post", type="primary", width='stretch'):
            for k in ["step", "topic", "url_input", "url_content", "outline",
                       "outline_approved", "draft", "draft_raw", "hero_variants",
                       "hero_chosen_idx", "inline_images", "social_snippets",
                       "exports", "error", "processing"]:
                if k in st.session_state:
                    if k in ("step",):
                        st.session_state[k] = "IDLE"
                    elif k in ("processing", "outline_approved"):
                        st.session_state[k] = False
                    else:
                        st.session_state[k] = None if k != "hero_variants" else []
            st.rerun()


# ---- Footer (always visible) ----
st.divider()
st.caption("Blog Writer Agent • Built with Agno framework • Skills: technical-blog-writer, imagegen")
