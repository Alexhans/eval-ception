# sketch-to-text exam

Evaluates the `sketch-to-text` Claude Code skill — converts handwritten PDF diagrams to Quarto (.qmd) with Mermaid diagrams.

## Setup

```bash
export BLOG_SAMPLES_DIR=/path/to/blog-samples
export I_KNOW_WHAT_IM_DOING=true
```

## Run

From this directory:
```bash
npx promptfoo eval --config sketch-to-text.yaml --verbose
```

View results:
```bash
npx promptfoo view
```

## Eval inputs & ground truth

- **Inputs:** `blog-samples/skills/sketch-to-text/evals/diagram-N.pdf`
- **Ground truth:** `blog-samples/skills/sketch-to-text/evals/ground-truth/diagram-N.expected.qmd`
- **Scoring rubric:** `blog-samples/skills/sketch-to-text/evals/README.md`

Ground truth files are human-reviewed drafts. Edit them to reflect your intended output before treating scores as authoritative.
