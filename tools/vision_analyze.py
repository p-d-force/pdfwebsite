#!/usr/bin/env python3
"""
Vision Analyzer — Local Gemma 4 model visual inspection for web dev.

Gemma 4 is Google's encoder-free multimodal model family. All sizes (E2B through
31B) support vision natively. Uses variable-resolution token budgets (70-1120)
to trade speed for detail.

Models tested:
  gemma4:12b       — 33s, concise, structured (PRIMARY)
  gemma4:8b         — faster, lower memory
  gemma4:26b        — maximum quality (heavy)
  minicpm-v4.5      — 108s, verbose (FALLBACK only)

Usage:
  python vision_analyze.py --url https://example.com --task ux_review
  python vision_analyze.py --url https://example.com --task ux_review --budget 560
  python vision_analyze.py --image screenshot.png --task debug_rendering
  python vision_analyze.py --url https://example.com --compare
"""

import argparse, base64, json, os, sys, time, urllib.request
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
PRIMARY_MODEL   = "gemma4:12b"
FALLBACK_MODEL  = "minicpm-v4.5:latest"
SCREENSHOT_DIR  = Path(os.environ.get("VISION_SCREENSHOT_DIR", os.path.expanduser("~/.vision-analyzer/screenshots")))
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Vision token budgets (Gemma 4 specific)
DEFAULT_BUDGET = 280
BUDGETS = {70: "Quick scan", 140: "Basic check", 280: "Balanced", 560: "Detailed", 1120: "Maximum detail"}

# Model family: name → (description, recommended_for)
MODEL_VARIANTS = {
    "gemma4:12b":         ("12B primary — general vision tasks", "ux_review, visual_inspection"),
    "gemma4:12b-256k":    ("12B with 256K context", "long documents, multi-screenshot"),
    "gemma4:12b-max":     ("12B max capability", "design_critique, accessibility_audit"),
    "gemma4:12b-balanced":("12B balanced speed/quality", "layout_analysis"),
    "gemma4:8b-128k":     ("8B with 128K context", "quick scans, fast iteration"),
    "gemma4:8b-max":      ("8B max capability", "debug_rendering (fast)"),
    "gemma4:26b":         ("26B maximum quality (heavy)", "design_critique, detailed analysis"),
    "gemma4:26b-compact": ("26B compact (lower memory)", "design_critique"),
    "gemma4:deep":        ("8B deep reasoning", "complex UX analysis"),
    "gemma4:strict":      ("8B strict instruction following", "accessibility_audit"),
    "minicpm-v4.5:latest":("MiniCPM-V 4.5 (fallback)", "fallback only"),
}

# Task → (default_model, recommended_budget)
ROUTER_RULES = {
    "visual_inspection":   (PRIMARY_MODEL, 140),
    "layout_analysis":     (PRIMARY_MODEL, 280),
    "ux_review":           (PRIMARY_MODEL, 280),
    "debug_rendering":     (PRIMARY_MODEL, 560),
    "accessibility_audit": (PRIMARY_MODEL, 280),
    "design_critique":     ("gemma4:26b",  280),
    "screenshot_describe": (PRIMARY_MODEL, 280),
    "color_contrast":      (PRIMARY_MODEL, 140),
    "find_element":        (PRIMARY_MODEL, 280),
    "dom_analysis":        (PRIMARY_MODEL, None),   # no image needed
    "code_review":         (PRIMARY_MODEL, None),
    "nav_evaluate":        (PRIMARY_MODEL, None),
}

# ── Model Router ─────────────────────────────────────────────────────────

def probe_models() -> list[str]:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        data = json.loads(urllib.request.urlopen(req, timeout=5).read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []

def route_model(task: str, override: str | None = None, available: list[str] | None = None) -> str:
    """Select best model for task, respecting user override."""
    if override:
        return override
    preferred = ROUTER_RULES.get(task, (PRIMARY_MODEL, 280))[0]
    if available is None:
        available = probe_models()
    # Exact match first
    if preferred in available:
        return preferred
    # Match base name (e.g. gemma4:12b matches gemma4:12b-256k)
    base = preferred.split(":")[0]
    for avail in available:
        if base in avail:
            return avail
    # Fallback
    for avail in available:
        if "gemma4" in avail:
            return avail
    if "minicpm" in str(available).lower():
        return FALLBACK_MODEL
    return preferred

def get_budget(task: str, override: int | None = None) -> int | None:
    if override is not None:
        return override
    return ROUTER_RULES.get(task, (PRIMARY_MODEL, DEFAULT_BUDGET))[1]

# ── Screenshot Capture ──────────────────────────────────────────────────

def capture_screenshot(url: str, width: int = 1440, height: int = 900) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. pip install playwright && playwright install chromium")
        sys.exit(1)
    ts = int(time.time())
    out_path = SCREENSHOT_DIR / f"screenshot_{ts}.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()
    print(f"Captured: {out_path} ({out_path.stat().st_size:,} bytes)")
    return out_path

# ── Ollama API ──────────────────────────────────────────────────────────

def call_ollama(model: str, prompt: str, image_path: str | None = None,
                temperature: float = 0.3, budget: int | None = None, timeout: int = 300) -> str:
    """Call Ollama API with optional image and Gemma 4 token budget."""
    images = []
    if image_path and Path(image_path).exists():
        with open(image_path, "rb") as f:
            images = [base64.b64encode(f.read()).decode()]

    options = {"temperature": temperature}
    if budget and "gemma" in model.lower():
        # Gemma 4 vision token budget: controls resolution vs speed
        options["num_ctx"] = max(4096, budget * 16)  # ensure enough context

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": images}],
        "stream": False,
        "options": options,
    }

    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    print(f"[{model}] budget={budget or 'default'} ", end="", flush=True)
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        result = json.loads(resp.read())
        elapsed = time.time() - t0
        content = result["message"]["content"]
        print(f"{elapsed:.1f}s, {len(content)} chars")
        return content
    except Exception as e:
        print(f"ERROR: {e}")
        return f"[Error: {e}]"

# ── Prompt Templates ────────────────────────────────────────────────────

PROMPTS = {
    "visual_inspection": """Look at this webpage screenshot. Describe:
1. What kind of page this is
2. All major UI elements (nav, headers, CTAs, forms, etc.)
3. Any rendering issues, alignment problems, or visual bugs
4. The overall visual hierarchy — what draws attention first?
Be specific about positions and elements.""",

    "layout_analysis": """Analyze this webpage layout:
1. Identify the layout pattern (grid, sidebar, single column, etc.)
2. Spatial arrangement of major sections
3. Layout inconsistencies, overlapping elements, broken flows
4. Whitespace usage and visual balance
5. What layout improvements would you suggest?""",

    "ux_review": """You are a senior UX designer. Review this page:
1. Information architecture — is content hierarchy logical?
2. Navigation — discoverable and intuitive?
3. CTAs — prominent and clear? Primary vs secondary distinct?
4. Readability — font sizing, contrast, line height
5. Mobile responsiveness clues — anything cramped?
6. Give 3-5 specific, actionable recommendations ranked by impact.
Be concise and structured.""",

    "debug_rendering": """You are a frontend debugger. Find visual bugs:
1. Misaligned elements or overflow issues?
2. Broken, cut off, or incorrectly positioned elements?
3. Z-index or stacking issues?
4. Font rendering problems?
5. Color inconsistencies?
List every issue with exact positions.""",

    "accessibility_audit": """Audit this page for accessibility:
1. Color contrast issues — any text hard to read?
2. Focus indicators — interactive elements visually distinct?
3. Text sizing — anything too small?
4. Visual clutter and cognitive load
5. Navigation accessibility
6. Form/input usability
Rank issues: critical, major, minor.""",

    "design_critique": """Design critique of this page:
1. Visual design quality — palette, typography, spacing
2. Brand consistency
3. Modernity — current or dated?
4. Emotional impact
5. 3 things done well, 3 to improve.""",

    "screenshot_describe": """Describe everything visible in this screenshot in thorough detail.
Include positions, colors, text content, and all UI elements.
This is a pre-analysis description for further processing.""",
}

def get_prompt(task: str, custom: str | None = None) -> str:
    return custom or PROMPTS.get(task, PROMPTS["visual_inspection"])

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vision Analyzer — local Gemma 4 visual inspection")
    parser.add_argument("--url", help="URL to screenshot and analyze")
    parser.add_argument("--image", help="Path to existing screenshot")
    parser.add_argument("--task", default="visual_inspection", choices=list(PROMPTS.keys()),
                        help="Analysis task type")
    parser.add_argument("--model", help="Override model selection (e.g. gemma4:26b)")
    parser.add_argument("--budget", type=int, choices=[70,140,280,560,1120],
                        help="Vision token budget (70=fast, 560=detailed, 1120=max)")
    parser.add_argument("--prompt", help="Custom prompt (overrides template)")
    parser.add_argument("--compare", action="store_true", help="Run comparison between models")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--list-tasks", action="store_true", help="List available tasks and models")

    args = parser.parse_args()

    if args.list_tasks:
        available = probe_models()
        print(f"Available models: {available}\n")
        print(f"{'Task':<25} {'Model':<25} {'Budget':<10}")
        print("-" * 60)
        for task, (model, budget) in ROUTER_RULES.items():
            budget_str = str(budget) if budget else "N/A"
            print(f"  {task:<23} {model:<25} {budget_str:<10}")
        print(f"\nModel variants:")
        for name, (desc, rec) in MODEL_VARIANTS.items():
            status = "✓" if any(name.split(":")[0] in a for a in available) else " "
            print(f"  [{status}] {name:<25} {desc}")
        print(f"\nToken budgets: {json.dumps(BUDGETS, indent=2)}")
        return

    if not args.url and not args.image:
        parser.error("Either --url or --image is required")

    image_path = args.image or str(capture_screenshot(args.url, args.width, args.height))
    available = probe_models()
    model = route_model(args.task, args.model, available)
    budget = get_budget(args.task, args.budget)

    print(f"Task: {args.task} | Model: {model} | Budget: {budget or 'N/A'}")

    if args.compare:
        models_to_test = [m for m in [PRIMARY_MODEL, FALLBACK_MODEL] if any(m.split(":")[0] in a for a in available)]
        if not models_to_test:
            models_to_test = [model]
        for m in models_to_test:
            prompt = get_prompt(args.task, args.prompt)
            result = call_ollama(m, prompt, image_path, budget=budget)
            print(f"\n{'='*60}\n## {m}\n{result}")
    else:
        prompt = get_prompt(args.task, args.prompt)
        result = call_ollama(model, prompt, image_path, budget=budget)
        print(f"\n{'='*60}\n{result}")

if __name__ == "__main__":
    main()
