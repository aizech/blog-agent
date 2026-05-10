"""Config page — edit config.yaml settings via the UI."""

from pathlib import Path

import streamlit as st
import yaml

from config import list_brands, load_brand, load_config

BRANDS_DIR = Path(__file__).resolve().parent.parent / "brands"

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

st.set_page_config(page_title="Config", page_icon="⚙️", layout="centered")

st.title("⚙️ Configuration")
st.caption("Changes are saved to `config.yaml` and take effect on the next run.")

cfg = load_config()
brand_names = list_brands()

# ---- Active brand (default) ----
if brand_names:
    active_brand_val = cfg.get("active_brand", brand_names[0])
    active_brand = st.selectbox(
        "Default brand",
        options=brand_names,
        index=brand_names.index(active_brand_val) if active_brand_val in brand_names else 0,
        help="Applied to all generated images unless overridden per post",
    )
else:
    active_brand = ""
    st.info("No brands found in brands/ — create one below.")

st.divider()

# ----------------------------------------------------------------
# LLM
# ----------------------------------------------------------------
st.markdown("## 🤖 LLM Model")

PROVIDERS = ["openai", "anthropic", "groq", "ollama", "google"]

llm_provider = st.selectbox(
    "Provider",
    options=PROVIDERS,
    index=PROVIDERS.index(cfg["llm"]["provider"]) if cfg["llm"]["provider"] in PROVIDERS else 0,
    help="Model provider. Make sure the corresponding API key is set in .env.",
)

PROVIDER_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    "anthropic": ["claude-opus-4-5", "claude-sonnet-4-5", "claude-3-5-haiku-latest", "claude-3-opus", "claude-3-sonnet"],
    "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma-7b-it", "llama3-8b-8192"],
    "ollama": ["llama3", "mistral", "gemma3", "phi3", "codellama"],
    "google": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
}

models_for_provider = PROVIDER_MODELS.get(llm_provider, [])
current_model = cfg["llm"]["model"]
# If current model not in list, add it as first option
if current_model not in models_for_provider:
    models_for_provider = [current_model] + list(models_for_provider)

llm_model = st.selectbox(
    "Model ID",
    options=models_for_provider,
    index=models_for_provider.index(current_model) if current_model in models_for_provider else 0,
    help=f"Available models for {llm_provider}",
)

st.divider()

# ----------------------------------------------------------------
# Hero images
# ----------------------------------------------------------------
st.markdown("## 🖼️ Hero Images")

IMAGE_MODELS = ["dall-e-3", "dall-e-2", "gpt-image-1", "gpt-image-1.5", "gpt-image-2", "gpt-image-1-mini"]
OUTPUT_FORMATS = ["png", "webp", "jpeg"]
BACKGROUNDS = ["(none)", "opaque", "transparent"]

col_a, col_b = st.columns(2)

with col_a:
    hero_model_val = cfg["image"]["hero"]["model"]
    hero_model = st.selectbox(
        "Model",
        options=IMAGE_MODELS,
        index=IMAGE_MODELS.index(hero_model_val) if hero_model_val in IMAGE_MODELS else 0,
        key="hero_model",
    )
    hero_is_gpt = hero_model.startswith("gpt-image")
    HERO_SIZES = ["1536x1024", "1024x1024", "1024x1536"] if hero_is_gpt else ["1792x1024", "1024x1024", "1024x1792"]
    hero_size_val = cfg["image"]["hero"]["size"]
    hero_size = st.selectbox(
        "Size",
        options=HERO_SIZES,
        index=HERO_SIZES.index(hero_size_val) if hero_size_val in HERO_SIZES else 0,
    )
    hero_output_format_val = cfg["image"]["hero"].get("output_format", "png")
    hero_output_format = st.selectbox(
        "Output format",
        options=OUTPUT_FORMATS,
        index=OUTPUT_FORMATS.index(hero_output_format_val) if hero_output_format_val in OUTPUT_FORMATS else 0,
        disabled=not hero_is_gpt,
        help="Only applies to GPT image models",
    )

with col_b:
    HERO_QUALITIES = ["high", "medium", "low"] if hero_is_gpt else ["hd", "standard"]
    hero_quality_val = cfg["image"]["hero"]["quality"]
    hero_quality = st.selectbox(
        "Quality",
        options=HERO_QUALITIES,
        index=HERO_QUALITIES.index(hero_quality_val) if hero_quality_val in HERO_QUALITIES else 0,
    )
    hero_variants = st.number_input(
        "Number of variants",
        min_value=1,
        max_value=6,
        value=int(cfg["image"]["hero"]["num_variants"]),
        step=1,
    )
    hero_bg_val = cfg["image"]["hero"].get("background", "(none)")
    hero_background = st.selectbox(
        "Background",
        options=BACKGROUNDS,
        index=BACKGROUNDS.index(hero_bg_val) if hero_bg_val in BACKGROUNDS else 0,
        disabled=not hero_is_gpt,
        help="Only applies to GPT image models. Transparent requires png/webp.",
    )

st.divider()

# ----------------------------------------------------------------
# Inline images
# ----------------------------------------------------------------
st.markdown("## 🔲 Inline Images")

col_c, col_d = st.columns(2)

with col_c:
    inline_model_val = cfg["image"]["inline"]["model"]
    inline_model = st.selectbox(
        "Model",
        options=IMAGE_MODELS,
        index=IMAGE_MODELS.index(inline_model_val) if inline_model_val in IMAGE_MODELS else 0,
        key="inline_model",
    )
    inline_is_gpt = inline_model.startswith("gpt-image")
    INLINE_SIZES = ["1024x1024", "1536x1024", "1024x1536"] if inline_is_gpt else ["1024x1024", "1792x1024", "1024x1792"]
    inline_size_val = cfg["image"]["inline"]["size"]
    inline_size = st.selectbox(
        "Size",
        options=INLINE_SIZES,
        index=INLINE_SIZES.index(inline_size_val) if inline_size_val in INLINE_SIZES else 0,
        key="inline_size",
    )
    inline_output_format_val = cfg["image"]["inline"].get("output_format", "png")
    inline_output_format = st.selectbox(
        "Output format",
        options=OUTPUT_FORMATS,
        index=OUTPUT_FORMATS.index(inline_output_format_val) if inline_output_format_val in OUTPUT_FORMATS else 0,
        disabled=not inline_is_gpt,
        help="Only applies to GPT image models",
        key="inline_output_format",
    )

with col_d:
    INLINE_QUALITIES = ["high", "medium", "low"] if inline_is_gpt else ["standard", "hd"]
    inline_quality_val = cfg["image"]["inline"]["quality"]
    inline_quality = st.selectbox(
        "Quality",
        options=INLINE_QUALITIES,
        index=INLINE_QUALITIES.index(inline_quality_val) if inline_quality_val in INLINE_QUALITIES else 0,
        key="inline_quality",
    )
    inline_max = st.number_input(
        "Max per session",
        min_value=0,
        max_value=10,
        value=int(cfg["image"]["inline"]["max_per_session"]),
        step=1,
    )
    inline_bg_val = cfg["image"]["inline"].get("background", "(none)")
    inline_background = st.selectbox(
        "Background",
        options=BACKGROUNDS,
        index=BACKGROUNDS.index(inline_bg_val) if inline_bg_val in BACKGROUNDS else 0,
        disabled=not inline_is_gpt,
        help="Only applies to GPT image models",
        key="inline_background",
    )

st.divider()

# ================================================================
# VISION (Image Analysis)
# ================================================================
st.markdown("## 👁️ Vision")
st.caption("Configure the vision-capable model used for image analysis and validation.")

VISION_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
]

vision_model_val = cfg.get("vision", {}).get("model", "gpt-4o")
vision_model = st.selectbox(
    "Vision model",
    options=VISION_MODELS,
    index=VISION_MODELS.index(vision_model_val) if vision_model_val in VISION_MODELS else 0,
    help="Model used for image analysis. gpt-4o is best for quality; gpt-4o-mini has higher vision token costs despite lower text pricing.",
)

vision_detail_val = cfg.get("vision", {}).get("detail", "auto")
vision_detail = st.selectbox(
    "Detail level",
    options=["auto", "low", "high"],
    index=["auto", "low", "high"].index(vision_detail_val) if vision_detail_val in ["auto", "low", "high"] else 0,
    help="low = 512x512 fixed (~85 tokens); high = full resolution; auto = let OpenAI decide",
)

vision_max_size_val = cfg.get("vision", {}).get("max_image_size", 2048)
vision_max_size = st.number_input(
    "Max image size (px)",
    min_value=512,
    max_value=4096,
    value=int(vision_max_size_val),
    step=256,
    help="Images larger than this will be resized before sending to the vision API.",
)

st.divider()

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
if st.button("💾 Save config", type="primary", width="stretch"):
    hero_cfg_out: dict = {
        "model": hero_model,
        "size": hero_size,
        "quality": hero_quality,
        "num_variants": int(hero_variants),
    }
    if hero_is_gpt:
        hero_cfg_out["output_format"] = hero_output_format
        if hero_background != "(none)":
            hero_cfg_out["background"] = hero_background

    inline_cfg_out: dict = {
        "model": inline_model,
        "size": inline_size,
        "quality": inline_quality,
        "max_per_session": int(inline_max),
    }
    if inline_is_gpt:
        inline_cfg_out["output_format"] = inline_output_format
        if inline_background != "(none)":
            inline_cfg_out["background"] = inline_background

    new_cfg = {
        "active_brand": active_brand,
        "llm": {
            "provider": llm_provider,
            "model": llm_model.strip(),
        },
        "image": {
            "hero": hero_cfg_out,
            "inline": inline_cfg_out,
        },
        "vision": {
            "model": vision_model,
            "detail": vision_detail,
            "max_image_size": int(vision_max_size),
        },
    }
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(new_cfg, f, default_flow_style=False, sort_keys=False)
    st.success("✅ Saved to config.yaml — restart the agent on the main page to apply LLM changes.")

st.divider()

# ================================================================
# BRAND MANAGER
# ================================================================
st.markdown("## 🎨 Brand Manager")

tab_edit, tab_new, tab_delete = st.tabs(["Edit brand", "New brand", "Delete brand"])

with tab_edit:
    if not brand_names:
        st.info("No brands yet — create one in the 'New brand' tab.")
    else:
        # Use a form approach that properly reloads when brand changes
        edit_brand_name = st.selectbox("Select brand to edit", brand_names, key="edit_brand_sel")
        
        # Load the selected brand fresh each time
        try:
            edit_brand = load_brand(edit_brand_name)
        except FileNotFoundError:
            edit_brand = {}
        
        # Get palette with defaults
        palette = edit_brand.get("palette", {})
        primary_color = palette.get("primary", "#1E3A5F")
        accent_color = palette.get("accent", "#00B4D8")
        bg_color = palette.get("background", "#F8F9FA")
        
        # Use the actual YAML values as defaults, not session state
        # This ensures switching brands always shows the correct data
        st.markdown(f"**Editing:** `{edit_brand_name}.yaml`")
        
        with st.form(key="edit_brand_form"):
            eb_name = st.text_input("Display name", value=edit_brand.get("name", ""))
            eb_style = st.text_area("Style description", value=edit_brand.get("style", ""), height=80)
            eb_tone = st.text_input("Tone", value=edit_brand.get("tone", ""))
            
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                eb_primary = st.color_picker("Primary", value=primary_color)
            with ec2:
                eb_accent = st.color_picker("Accent", value=accent_color)
            with ec3:
                eb_bg = st.color_picker("Background", value=bg_color)
            
            eb_logo = st.text_input("Logo path (optional)", value=edit_brand.get("logo_path", ""))
            eb_ref = st.text_input("Reference image path (optional)", value=edit_brand.get("reference_image", ""))
            
            val = edit_brand.get("validation", {})
            ev_enabled = st.checkbox("Enable vision validation", value=val.get("enabled", True))
            ev1, ev2 = st.columns(2)
            with ev1:
                ev_score = st.number_input("Min score (0-10)", min_value=0, max_value=10, value=int(val.get("min_score", 7)))
            with ev2:
                ev_retries = st.number_input("Max retries", min_value=0, max_value=5, value=int(val.get("max_retries", 2)))
            
            submitted = st.form_submit_button("💾 Save brand", type="primary")
            
            if submitted:
                updated = {
                    "name": eb_name.strip(),
                    "style": eb_style.strip(),
                    "tone": eb_tone.strip(),
                    "palette": {"primary": eb_primary, "accent": eb_accent, "background": eb_bg},
                    "logo_path": eb_logo.strip(),
                    "reference_image": eb_ref.strip(),
                    "validation": {"enabled": ev_enabled, "min_score": int(ev_score), "max_retries": int(ev_retries)},
                }
                brand_path = BRANDS_DIR / f"{edit_brand_name}.yaml"
                with open(brand_path, "w") as f:
                    yaml.dump(updated, f, default_flow_style=False, sort_keys=False)
                st.success(f"✅ Saved brands/{edit_brand_name}.yaml")
                st.rerun()

with tab_new:
    nb_slug = st.text_input("Brand slug (filename, lowercase, no spaces)", placeholder="mybrand", key="nb_slug")
    nb_name = st.text_input("Display name", placeholder="My Brand", key="nb_name")
    nb_style = st.text_area("Style description", height=80, key="nb_style")
    nb_tone = st.text_input("Tone", key="nb_tone")
    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        nb_primary = st.color_picker("Primary", value="#1E3A5F", key="nb_primary")
    with nc2:
        nb_accent = st.color_picker("Accent", value="#00B4D8", key="nb_accent")
    with nc3:
        nb_bg = st.color_picker("Background", value="#F8F9FA", key="nb_bg")

    if st.button("➕ Create brand", type="primary", key="nb_create"):
        slug = nb_slug.strip().lower().replace(" ", "-")
        if not slug:
            st.error("Slug is required.")
        elif (BRANDS_DIR / f"{slug}.yaml").exists():
            st.error(f"Brand '{slug}' already exists.")
        else:
            new_brand = {
                "name": nb_name.strip() or slug,
                "style": nb_style.strip(),
                "tone": nb_tone.strip(),
                "palette": {"primary": nb_primary, "accent": nb_accent, "background": nb_bg},
                "logo_path": "",
                "reference_image": "",
                "validation": {"enabled": True, "min_score": 7, "max_retries": 2},
            }
            BRANDS_DIR.mkdir(exist_ok=True)
            with open(BRANDS_DIR / f"{slug}.yaml", "w") as f:
                yaml.dump(new_brand, f, default_flow_style=False, sort_keys=False)
            st.success(f"✅ Created brands/{slug}.yaml")
            st.rerun()

with tab_delete:
    if not brand_names:
        st.info("No brands to delete.")
    else:
        del_brand = st.selectbox("Select brand to delete", brand_names, key="del_brand_sel")
        st.warning(f"This will permanently delete **brands/{del_brand}.yaml**.")
        if st.button("🗑️ Delete brand", type="primary", key="del_confirm"):
            brand_path = BRANDS_DIR / f"{del_brand}.yaml"
            if brand_path.exists():
                brand_path.unlink()
                st.success(f"Deleted brands/{del_brand}.yaml")
                st.rerun()
            else:
                st.error("File not found.")
