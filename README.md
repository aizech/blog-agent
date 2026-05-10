# Blog Writer Agent

A powerful Streamlit-based blog writing application powered by the **Agno framework** and **OpenAI**. Generate technical blog posts with AI-assisted outlines, brand-aligned hero images, inline illustrations, and multi-format exports.

## Features

### Content Generation
- **AI-Powered Outlines**: Generate structured blog post outlines from a topic or URL
- **Draft Writing**: Streamed content generation with the technical-blog-writer skill
- **Markdown Editor**: Edit drafts in-browser with `streamlit-ace` before image generation
- **URL Content Fetching**: Extract and rewrite content from existing articles

### Image Generation
- **Hero Images**: Wide landscape images (1536x1024) for page headers with multiple variants
- **Inline Images**: Square illustrations (1024x1024) for blog sections
- **Brand Integration**: Multi-brand system with configurable palettes, styles, and tones
- **Vision Support**: GPT-4o Vision for image analysis and validation

### Workflow
1. **Input**: Enter a topic idea or provide a URL to rewrite
2. **Outline**: Review and edit the generated outline
3. **Draft**: Streamed generation with live preview
4. **Edit**: Refine content in the markdown editor
5. **Hero Images**: Generate and select hero image variants
6. **Inline Images**: Generate illustrations for key sections
7. **Export**: Save with embedded images, generate social snippets

### Archive & Organization
- **Session-Based Files**: All files saved with consistent timestamps (`YYYYMMDD_HHMMSS`)
- **Archive Page**: Browse posts and related images grouped by session
- **Auto-Save**: Drafts automatically saved after generation
- **Prompt History**: Image generation prompts saved to YAML files

## Installation

```bash
# Clone or navigate to the project
cd blog-agent

# Install dependencies (recommended: use uv)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# - OPENAI_API_KEY (required for image generation and LLM)
```

## Usage

```bash
# Run the Streamlit application
streamlit run Home.py
```

The app will open at `http://localhost:8501`

## Project Structure

```
blog-agent/
├── Home.py                    # Main Streamlit application
├── config.yaml                # App configuration (LLM, image models, vision)
├── config.py                  # Configuration loader with defaults
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
├── agent/                     # Agent orchestration and tools
│   ├── orchestrator.py       # Agno agent setup
│   ├── tools.py              # File saving, URL fetching tools
│   └── workflow.py           # Blog generation workflow
├── pages/                     # Streamlit multi-page setup
│   ├── 2_⚙️_Config.py        # Configuration UI
│   └── 3_📁_Archive.py       # Archive browser
├── skills/                    # Specialized skills
│   ├── image_gen.py          # DALL-E / GPT image generation
│   ├── vision.py             # GPT-4o Vision analysis
│   ├── brand_visual.py       # Brand validation
│   └── technical_blog_writer/ # Blog writing skill
├── brands/                    # Brand configuration files
│   ├── anthropic.yaml        # Example brand
│   └── corpusanalytica.yaml  # Your custom brand
├── output/                    # Generated content
│   ├── posts/                # Saved blog posts (.md)
│   ├── images/               # Generated images (.png)
│   └── prompts/              # Image prompts (.yaml)
└── templates/                # Export templates
```

## Configuration

### config.yaml

```yaml
active_brand: corpusanalytica

llm:
  provider: openai
  model: gpt-4o-mini

image:
  hero:
    model: gpt-image-2      # or dall-e-3
    size: 1536x1024
    quality: high
    num_variants: 1
    output_format: png
  inline:
    model: gpt-image-2
    size: 1024x1024
    quality: high
    max_per_session: 2
    output_format: png

vision:
  model: gpt-4o             # Vision model for analysis
  detail: auto              # auto | low | high
  max_image_size: 2048
```

### Brand Configuration

Create custom brand files in `brands/`:

```yaml
name: CorpusAnalytica
style: Minimalist monochrome abstract composition...
tone: particle simulation, neural network aesthetics...
palette:
  primary: '#1C1917'
  accent: '#E27E03'
  background: '#FAF8F5'
logo_path: https://example.com/logo.png
reference_image: https://example.com/reference.png
validation:
  enabled: true
  min_score: 7
  max_retries: 2
```

## Image Models Supported

- **GPT Image Models**: `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`
  - Returns base64 encoded images
  - Supports `output_format` and `background` parameters
  
- **DALL-E Models**: `dall-e-3`, `dall-e-2`
  - Returns image URLs
  - Supports `hd` and `standard` quality

## Vision Configuration

Vision models analyze generated images for brand alignment:

| Model | Quality | Best For |
|---|---|---|
| `gpt-4o` | High | Detailed analysis, brand validation |
| `gpt-4o-mini` | High | Cost-conscious (higher vision token cost) |
| `gpt-4.1` | High | Balanced performance |
| `gpt-4.1-mini` | Medium | Fast processing |
| `gpt-4.1-nano` | Basic | Quick checks |

**Detail levels:**
- `low`: 512x512 fixed (~85 tokens)
- `high`: Full resolution
- `auto`: Let OpenAI decide

## Output File Naming

All files use consistent session timestamps:

```
output/
├── posts/
│   ├── blog-20250110_143022.md          # Final saved post
│   └── blog-20250110_143022-auto.md     # Auto-saved draft
├── images/
│   ├── hero-20250110_143022-v1.png      # Hero variant 1
│   ├── hero-20250110_143022-v2.png      # Hero variant 2
│   ├── inline-20250110_143022-1.png     # Inline image 1
│   └── inline-20250110_143022-2.png     # Inline image 2
└── prompts/
    └── prompts-20250110_143022.yaml      # Generation prompts
```

## Archive Page

Browse all generated content by session:

- **Sessions**: Grouped by timestamp
- **Posts**: Preview content, download markdown
- **Images**: View hero and inline images per session
- **Stats**: Total sessions, posts, and images

## Dependencies

- **agno** ≥2.6.5 — Agent framework
- **streamlit** ≥1.40 — Web UI
- **openai** ≥1.0 — Image generation and LLM
- **streamlit-ace** ≥0.1.1 — Markdown editor
- **beautifulsoup4**, **readability-lxml** — URL content extraction
- **python-docx**, **markdown** — Export formats
- **Pillow** — Image processing
- **PyYAML** ≥6.0 — Configuration files

## Environment Variables

```bash
OPENAI_API_KEY=sk-...           # Required
# Optional: Other API keys if extending
```

## License

MIT License - See repository for details.

## Credits

- Built with [Agno](https://github.com/agno-agi/agno) framework
- Images generated via OpenAI API
- UI powered by Streamlit
