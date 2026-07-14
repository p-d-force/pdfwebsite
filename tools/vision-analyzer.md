---
title: Vision Analyzer
name: vision-analyzer
version: 2.0.0
author: parentdataforce
description: Local Gemma 4 vision models for web dev — visual inspection, UI/UX review, layout analysis, debug rendering, accessibility audit. Supports token budgets, model variants, and model routing.
model_flags:
  - tool:reading
triggers:
  - user asks for visual inspection or screenshot analysis
  - "UI/UX review", "design critique", "accessibility audit"
  - "debug rendering", "find visual bugs", "check layout"
  - "compare models for vision", "use vision to analyze"
  - "look at this page", "analyze the screenshot"
  - questions about Gemma model capabilities or token budgets
agent_hints:
  - Run `python tools/vision_analyze.py --url <url> --task <task>` for visual analysis
  - Use `--budget 280` for detailed analysis, `--budget 70` for quick scans
  - Gemma 4 models support variable resolution via token budgets (70-1120)
  - All Gemma 4 sizes (E2B through 31B) support vision natively
  - For text-only tasks (nav eval, DOM analysis), gemma4:12b suffices — no image needed
---

# Vision Analyzer — Gemma 4 Models

## Gemma 4 Architecture

Gemma 4 is Google's encoder-free multimodal model family. Unlike MiniCPM-V (which uses a separate vision encoder), Gemma 4 projects raw image patches directly into the LLM's embedding space. This means:

- **Faster inference** — no separate encoder forward pass
- **Unified fine-tuning** — vision and text are trained together
- **All sizes support vision** — E2B, E4B, 12B, 26B, 31B

### Locally Available Models

| Model | Size | Memory | Context | Best For |
|-------|------|--------|---------|----------|
| `gemma4:12b` | 7.6 GB | ~27 GB BF16 / ~7 GB Q4 | 256K | **Primary** — general vision tasks |
| `gemma4:12b-256k` | 7.6 GB | same | 256K | Long-context vision analysis |
| `gemma4:12b-max` | 7.6 GB | same | 256K | Maximum capability variant |
| `gemma4:12b-balanced` | 7.6 GB | same | 256K | Balanced speed/quality |
| `gemma4:8b-128k` | 9.6 GB | ~18 GB BF16 | 128K | Faster, lower memory |
| `gemma4:8b-max` | 9.6 GB | same | 128K | Max quality at 8B size |
| `gemma4:26b` | 17 GB | ~58 GB BF16 | 256K | Maximum quality (heavy) |
| `gemma4:26b-compact` | 17 GB | same | 256K | 26B with lower memory |
| `gemma4:deep` | 9.6 GB | ~18 GB BF16 | varies | Deep reasoning variant |
| `gemma4:strict` | 9.6 GB | ~18 GB BF16 | varies | Strict instruction following |
| `minicpm-v4.5:latest` | 6.1 GB | varies | varies | **Fallback** — only if Gemma unavailable |

### Vision Token Budgets

Gemma 4 supports variable resolution via **token budgets**. Higher = more detail, lower = faster.

| Budget | Use Case | Speed |
|--------|----------|-------|
| **70** | Quick scan — "is the page loading?" | Fastest |
| **140** | Basic layout check, element presence | Fast |
| **280** | UX review, contrast check, most tasks | Balanced |
| **560** | Detailed debugging, small text OCR | Slow |
| **1120** | Fine detail, tiny elements, dense layouts | Slowest |

**How it works:** The budget controls how many visual tokens the image is split into. A budget of 280 generates up to 2,520 patches (280 × 9) which are then compressed into 280 final embeddings. The model charges ~256 tokens per image regardless of budget.

## Usage

```bash
# Basic: analyze a URL with default budget (280)
python tools/vision_analyze.py --url https://example.com --task ux_review

# High detail: use budget 560 for dense page analysis
python tools/vision_analyze.py --url https://example.com --task debug_rendering --budget 560

# Quick scan: budget 70 for a fast pass
python tools/vision_analyze.py --url https://example.com --task visual_inspection --budget 70

# Use a specific model variant
python tools/vision_analyze.py --url https://example.com --model gemma4:26b --task design_critique

# Compare two models
python tools/vision_analyze.py --url https://example.com --compare

# Analyze existing screenshot
python tools/vision_analyze.py --image screenshot.png --task accessibility_audit

# Text-only analysis (no image needed)
python tools/vision_analyze.py --task nav_evaluate
# (prompts for DOM text input)

# List available tasks and models
python tools/vision_analyze.py --list-tasks
```

## Tasks & Model Routing

| Task | Best Model | Budget | Description |
|------|-----------|--------|-------------|
| `visual_inspection` | gemma4:12b | 140 | General page description |
| `layout_analysis` | gemma4:12b | 280 | Layout pattern, spacing, balance |
| `ux_review` | gemma4:12b | 280 | Full UX audit with ranked recommendations |
| `debug_rendering` | gemma4:12b | 560 | Visual bug detection (high detail) |
| `accessibility_audit` | gemma4:12b | 280 | Contrast, focus, readability |
| `design_critique` | gemma4:12b | 280 | Visual design quality review |
| `screenshot_describe` | gemma4:12b | 280 | Thorough image description |
| `dom_analysis` | gemma4:12b | — | Text-only DOM structure (no image) |
| `code_review` | gemma4:12b | — | HTML/CSS review (no image) |
| `nav_evaluate` | gemma4:12b | — | Navigation structure (no image) |

## Capability Reference

### What Gemma 4 Vision Excels At
- **Object detection** — "find the login button", "locate all CTAs"
- **OCR** — reading text in screenshots, error messages, console output
- **Visual QA** — "what color is the donate button?", "is the nav sticky?"
- **Layout understanding** — spatial relationships between elements
- **Cross-image reasoning** — comparing two screenshots (before/after)
- **Variable resolution** — trade speed for detail via token budget

### Prompting Best Practices
1. **Images BEFORE text** — Gemma 4 processes images more accurately when they appear first
2. **Be specific** — "describe the nav layout" > "what do you see?"
3. **Provide constraints** — "list exactly 3 improvements" > "what should I improve?"
4. **Use higher budgets for detail** — OCR, small text, dense layouts need 560+
5. **Iterate** — start with budget 140, increase if details are missed

### Things to Avoid
- Expecting exact pixel counts for tiny elements
- Vague prompts like "generate something from this image"
- Using MiniCPM-V when Gemma 4 is available (3x slower, lower quality)

## Model Router Logic

```
1. Check available Ollama models
2. If gemma4:12b available → PRIMARY for all vision tasks
3. If gemma4:8b available → use for quick scans (budget 70-140)
4. If gemma4:26b available → use for design critique, detailed analysis
5. If only minicpm-v4.5 available → FALLBACK
6. Text-only tasks → any gemma4 variant (no vision needed)
```

## Prompt Templates

Each task has a tailored prompt in `vision_analyze.py`. The templates follow Gemma 4 best practices: specific, constrained, with clear output structure expectations. To see or customize, read the `PROMPTS` dict in the script.

## Comparison Results (tested 2026-07-14)

Same nav screenshot, visual_inspection prompt:

| Metric | gemma4:12b | minicpm-v4.5 |
|--------|-----------|-------------|
| Speed | 32.8s | 108.0s |
| Structure | Bullet points, clear sections | Flowing prose |
| Accuracy | High — identified all elements | High but less structured |
| Recommendations | 4 specific, actionable | Mixed quality |

**Verdict:** Gemma 4 12B is 3.3x faster with better output. Use it exclusively unless unavailable.

## Integration with Project

This tool complements the browser-based tools:
- **DOM inspection** (`tab.evaluate()`) — exact element positions, computed styles
- **Vision analysis** (`vision_analyze.py`) — visual impression, UX quality, design feedback
- **Use together** — DOM for precision, vision for human judgment
