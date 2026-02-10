# DeepEval Tests

Tests for the AI Evals website using [DeepEval](https://docs.confident-ai.com/).

## Caveat (In Construction)

This DeepEval path is a secondary example and still in construction.
For launch/default usage, prefer `promptfoo/`.

`test_questions.py` runs 7 pytest tests total, but DeepEval's metric summary may show only
the 2 LLM-as-judge (GEval) tests because deterministic checks run as plain pytest assertions.

## Setup

From repo root:

```bash
pip install -e ".[deepeval]"
```

## Run tests

```bash
cd deepeval
deepeval test run test_questions.py
```

With verbose output (shows intermediate metric steps):

```bash
deepeval test run test_questions.py -v
```

With parallel execution:

```bash
deepeval test run test_questions.py -v -n 4
```

## Configuration

The tests use the shared baseline agent from `eval_ception_core`. Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://ai-evals.io` | Target website |
| `OLLAMA_MODEL` | `qwen3:8b` | Agent model |
| `JUDGE_MODEL` | `deepseek-r1:14b` | Ollama judge model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |

Example running against localhost:

```bash
BASE_URL=http://localhost:3000 deepeval test run test_questions.py
```

## Test cases

1. **Who created this website?** - Should mention Alex Guglielmone Nemi
2. **What tools are open source?** - Should include Promptfoo/DeepEval and not include Braintrust/Langsmith
3. **Does promptfoo have built-in caching?** - Should start with yes
4. **Does deepeval have built-in caching?** - Should start with no
5. **Does Ragas have confirmed support for streaming evaluation?** - Should start with unknown
6. **What methodology does this website use to evaluate tools?** - LLM-as-judge
7. **How does it explain evals to different audiences?** - LLM-as-judge

## Notes

- DeepEval uses LLM-as-judge (GEval metric) only for the non-deterministic methodology/audience tests
- The judge model (`deepseek-r1:14b`) is intentionally different from the agent model (`qwen3:8b`) to avoid self-evaluation bias
- Uses `OllamaModel` directly - no `deepeval set-ollama` CLI setup needed
- Results are stored locally (`.deepeval/` dir) - the "view on website" prompt is just an upsell, nothing is uploaded without an API key
- To disable anonymous telemetry: `deepeval telemetry disable`
