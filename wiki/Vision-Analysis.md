# Vision Analysis

Local vision model integration for UI/UX review, accessibility auditing, and visual debugging. Uses Gemma 4 via Ollama — no cloud API calls.

## Architecture

Gemma 4 is Google's encoder-free multimodal model. Unlike traditional vision models that use a separate vision encoder, Gemma 4 projects raw image patches directly into the LLM's embedding space. This means:

- Faster inference (no separate encoder pass)
- All sizes support vision (8B, 12B, 26B, 31B)
- Variable resolution via token budgets

## Available Models

| Model | Size | Best For |
|---|---|---|
| `gemma4:12b` | 7.6 GB | Primary — general vision tasks |
| `gemma4:8b-128k` | 9.6 GB | Faster, lower memory |
| `gemma4:26b` | 17 GB | Maximum quality (heavy) |
| `minicpm-v4.5` | 6.1 GB | Fallback only (3.3x slower) |

## Token Budgets

Gemma 4 supports variable resolution:

| Budget | Use Case | Speed |
|---|---|---|
| 70 | Quick scan — "is the page loading?" | Fastest |
| 140 | Basic layout check | Fast |
| 280 | UX review, contrast check | Balanced |
| 560 | Detailed debugging, small text OCR | Slow |
| 1120 | Fine detail, dense layouts | Slowest |

## Tasks

```bash
# UX review with balanced detail
python tools/vision_analyze.py --url http://localhost:8081/ --task ux_review

# High-detail debug
python tools/vision_analyze.py --url http://localhost:8081/ --task debug_rendering --budget 560

# Quick scan
python tools/vision_analyze.py --url http://localhost:8081/ --task visual_inspection --budget 70

# Compare models
python tools/vision_analyze.py --url http://localhost:8081/ --compare

# Analyze existing screenshot
python tools/vision_analyze.py --image screenshot.png --task accessibility_audit

# List all tasks
python tools/vision_analyze.py --list-tasks
```

| Task | Budget | Purpose |
|---|---|---|
| `visual_inspection` | 140 | General page description |
| `layout_analysis` | 280 | Spacing, balance, patterns |
| `ux_review` | 280 | Full UX audit with ranked recommendations |
| `debug_rendering` | 560 | Visual bug detection |
| `accessibility_audit` | 280 | Contrast, focus, readability |
| `design_critique` | 280 | Visual design quality |
| `screenshot_describe` | 280 | Thorough image description |
| `dom_analysis` | — | Text-only DOM structure |
| `code_review` | — | HTML/CSS review (no image) |
| `nav_evaluate` | — | Navigation structure (no image) |

## Prompting Best Practices

1. Images BEFORE text — Gemma 4 processes images more accurately first
2. Be specific — "describe the nav layout" > "what do you see?"
3. Provide constraints — "list exactly 3 improvements"
4. Higher budgets for detail — OCR and small text need 560+
5. Iterate — start at 140, increase if details missed

## Performance

Gemma 4 12B vs MiniCPM-V 4.5 on same nav screenshot:

| Metric | Gemma 4 12B | MiniCPM-V 4.5 |
|---|---|---|
| Speed | 32.8s | 108.0s |
| Structure | Bullet points | Flowing prose |
| Accuracy | High | High but less structured |

Gemma 4 is 3.3x faster. Use it exclusively unless unavailable.
