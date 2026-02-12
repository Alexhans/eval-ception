# Promptfoo Evals

Tests for AI-Evals website question answering using Promptfoo.

## Prerequisites

From repo root:

```bash
pip install -e .
```

For local-model path (`ollama_agent`) only:

```bash
ollama pull qwen3:8b
ollama pull deepseek-r1:14b
```

These are tested defaults in this repo (agent=`qwen3:8b`, grader=`deepseek-r1:14b`).
You can use the same model for both agent and grader if preferred.

## Quick run

```bash
cd promptfoo
```

Smoke test (single deterministic question):

```bash
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^ollama_agent$" -n 1 --verbose
```

Full exam (all 7 tests):

```bash
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^ollama_agent$" --verbose
```

Open results:

```bash
npx promptfoo view
```

## Provider labels

Use `--filter-providers` with one of:
- `^ollama_agent$`
- `^codex$`
- `^claude$`
- `^opencode_ai$`

Examples:

```bash
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$"
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^claude$"
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^opencode_ai$"
```

Override grader model:

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434 \
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$" --grader "ollama:chat:deepseek-r1:14b"
```

Custom/OpenAI-compatible grader URL example:

```bash
OPENAI_API_KEY=your-key OPENAI_BASE_URL=https://your-grader-endpoint/v1 \
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$" --grader "openai:chat:gpt-4.1-mini"
```

No-API grader path (use CLI wrapper as grader):

```bash
export I_KNOW_WHAT_IM_DOING=true
export CLI_GRADER_AGENT=codex
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$" --grader "python:grader_provider.py"
```

CI shorthand (same behavior, less explicit acknowledgment):

```bash
I_KNOW_WHAT_IM_DOING=true CLI_GRADER_AGENT=codex \
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$" --grader "python:grader_provider.py"
```

## CLI wrapper notes

For CLI wrapper providers (`codex`, `claude`, `opencode_ai`):
- Set `I_KNOW_WHAT_IM_DOING=true`
- Understand these wrappers execute external CLIs and may inherit their permissions
- Prefer `ollama_agent`/`baseline-agent` path for safer local evaluation

Standalone wrapper example:

```bash
export I_KNOW_WHAT_IM_DOING=true
wrapped-cli-agent --agent codex --json "What is this site about?"
```

Standalone grader wrapper example:

```bash
export I_KNOW_WHAT_IM_DOING=true
wrapped-cli-grader --agent codex --json "Return PASS if this answer satisfies the rubric: ..."
```

Localhost target example:

```bash
wrapped-cli-agent --agent codex --url http://127.0.0.1:1234 --json "What is this site about?"
```

To run a local target site:

```bash
git clone https://github.com/Alexhans/ai-evals
cd ai-evals/evals_site/_site
python -m http.server 1234
```

## Configuration summary

Single source of truth: `promptfooconfig.yaml`.

Provider labels currently configured:

- `ollama_agent` via `python:ollama_provider.py`
- `codex` via `file://promptfoo_provider_codex.py`
- `claude` via `file://promptfoo_provider_claude.py`
- `opencode_ai` via `file://promptfoo_provider_opencode.py`
- CLI-based grader adapter via `python:grader_provider.py` (optional)

Shared baseline agent env vars:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://ai-evals.io` | Target website |
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model |
| `MAX_PAGES` | `10` | Max pages to crawl |

Run against localhost:

```bash
BASE_URL=http://localhost:3000 npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^ollama_agent$"
```

## Temporary: Airflow Translation Exam Example

This repo also includes a separate, in-progress Airflow localization example.

- Exam config: `exams/airflow-localizer-es/promptfooconfig.yaml`
- Cert JSON: `certs/airflow-localizer-es/airflow-es-localizer-exam-pydantic-agent.cert.json`
- Quick guide: `docs/start-here.md`

This section is temporary and does not replace the main "eval this site" workflow above.
