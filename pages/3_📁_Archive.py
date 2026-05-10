"""Archive page — browse all saved blog posts and their images by session."""

import re
from datetime import datetime
from pathlib import Path

import streamlit as st

# Paths
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
POSTS_DIR = OUTPUT_DIR / "posts"
IMAGES_DIR = OUTPUT_DIR / "images"

st.set_page_config(page_title="Archive", page_icon="📁", layout="wide")

st.title("📁 Archive")
st.caption("Browse all saved blog posts and their related images by session.")

# Ensure directories exist
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# ---- Helper functions ----
def extract_timestamp_from_filename(filename: str) -> str:
    """Extract timestamp from filename like blog-20250110_143022.md or hero-20250110_143022-v1.png"""
    # Match pattern: name-YYYYMMDD_HHMMSS or name-YYYYMMDD_HHMMSS-suffix
    match = re.search(r'(\d{8}_\d{6})', filename)
    return match.group(1) if match else ""


def get_all_sessions() -> dict[str, dict]:
    """Group all posts and images by session timestamp."""
    sessions = {}

    # Scan posts
    for md_file in POSTS_DIR.glob("*.md"):
        ts = extract_timestamp_from_filename(md_file.name)
        if ts:
            if ts not in sessions:
                sessions[ts] = {"post": None, "images": [], "timestamp": ts}
            content = md_file.read_text(encoding="utf-8")
            # Extract title from first heading
            title = "Untitled"
            for line in content.split("\n")[:10]:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            sessions[ts]["post"] = {
                "filename": md_file.name,
                "title": title,
                "path": md_file,
                "size": len(content),
                "modified": md_file.stat().st_mtime,
            }

    # Scan images
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif"]:
        for img in IMAGES_DIR.glob(ext):
            ts = extract_timestamp_from_filename(img.name)
            if ts:
                if ts not in sessions:
                    sessions[ts] = {"post": None, "images": [], "timestamp": ts}
                sessions[ts]["images"].append(img)

    # Scan subdirectories
    for subdir in IMAGES_DIR.iterdir():
        if subdir.is_dir():
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                for img in subdir.glob(ext):
                    ts = extract_timestamp_from_filename(img.name)
                    if ts:
                        if ts not in sessions:
                            sessions[ts] = {"post": None, "images": [], "timestamp": ts}
                        if img not in sessions[ts]["images"]:
                            sessions[ts]["images"].append(img)

    return sessions


def format_timestamp(ts: str) -> str:
    """Format timestamp string for display."""
    try:
        dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts


# ---- Main content ----
sessions = get_all_sessions()
sorted_sessions = sorted(sessions.items(), key=lambda x: x[0], reverse=True)  # Newest first

if not sessions:
    st.info("No posts in archive yet. Generate and save a blog post to see it here.")
    st.stop()

# Sidebar: Session list
with st.sidebar:
    st.markdown("### 📄 Blog Sessions")
    st.caption(f"{len(sessions)} session(s) found")

    for ts, session in sorted_sessions:
        post = session.get("post")
        if post:
            label = f"{post['title'][:35]}..." if len(post['title']) > 35 else post['title']
            icon = "📄"
        else:
            label = f"Images only ({len(session['images'])} images)"
            icon = "🖼️"

        display_label = f"{icon} {format_timestamp(ts)}"
        if st.button(display_label, key=f"session_{ts}", width='stretch'):
            st.session_state.selected_session = ts
            st.rerun()

# Default selection
if 'selected_session' not in st.session_state or st.session_state.selected_session not in sessions:
    st.session_state.selected_session = sorted_sessions[0][0]

selected_session = sessions[st.session_state.selected_session]
selected_post = selected_session.get("post")

# Display session
col1, col2 = st.columns([2, 1])

with col1:
    if selected_post:
        post_content = selected_post['path'].read_text(encoding="utf-8")
        st.markdown(f"## {selected_post['title']}")
        st.caption(f"Session: `{st.session_state.selected_session}` • File: `{selected_post['filename']}`")

        # Content preview
        with st.expander("📝 Post Content", expanded=True):
            st.markdown(post_content[:3000] + ("..." if len(post_content) > 3000 else ""))

        # Full download
        st.download_button(
            "⬇️ Download Markdown",
            data=post_content,
            file_name=selected_post['filename'],
            mime="text/markdown",
            width='stretch',
        )
    else:
        st.info("This session has no blog post saved — only images.")

with col2:
    st.markdown("### 🖼️ Related Images")

    session_images = selected_session.get("images", [])

    if session_images:
        st.caption(f"{len(session_images)} image(s) in this session")

        # Hero images (sorted first)
        hero_images = [img for img in session_images if "hero-" in img.name.lower()]
        inline_images = [img for img in session_images if "inline-" in img.name.lower()]
        other_images = [img for img in session_images if img not in hero_images and img not in inline_images]

        if hero_images:
            st.markdown("**🎨 Hero Images**")
            for img_path in hero_images:
                try:
                    st.image(str(img_path), caption=f"Hero: {img_path.name}", width='stretch')
                except Exception:
                    st.text(f"📷 {img_path.name}")

        if inline_images:
            st.markdown("**🖼️ Inline Images**")
            cols = st.columns(2)
            for i, img_path in enumerate(inline_images):
                with cols[i % 2]:
                    try:
                        st.image(str(img_path), caption=f"Inline {i+1}", width='stretch')
                    except Exception:
                        st.text(f"📷 {img_path.name}")

        if other_images:
            st.markdown("**📁 Other Images**")
            cols = st.columns(2)
            for i, img_path in enumerate(other_images[:6]):
                with cols[i % 2]:
                    try:
                        st.image(str(img_path), caption=img_path.name, width='stretch')
                    except Exception:
                        st.text(f"📷 {img_path.name}")
    else:
        st.caption("No images in this session.")

st.divider()

# Archive stats
total_posts = len([s for s in sessions.values() if s.get("post")])
total_images = sum(len(s.get("images", [])) for s in sessions.values())
total_size_kb = sum(
    s["post"]["size"] for s in sessions.values() if s.get("post")
) / 1024

col_stats1, col_stats2, col_stats3 = st.columns(3)
with col_stats1:
    st.metric("Total Sessions", len(sessions))
with col_stats2:
    st.metric("Total Posts", total_posts)
with col_stats3:
    st.metric("Total Images", total_images)
