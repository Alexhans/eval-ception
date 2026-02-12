# Langfuse Evals

Tests for the AI Evals website using [Langfuse](https://langfuse.com/) with a self-hosted Docker setup.

Like DeepEval, this uses pytest for test execution. Traces and scores are recorded in the Langfuse UI for observability.

## Setup

**Important:** You must create a `.env` file before starting Docker — without it, all secrets are blank and Postgres won't start.

```bash
cp langfuse/.env.example langfuse/.env    # required
docker compose -f langfuse/docker-compose.yml up -d
```

Langfuse UI will be available at `http://localhost:3000`.

### Why `.env`?

The Docker stack needs secrets (encryption key, database password, API keys).
`.env.example` ships with working defaults for localhost — copy it and go.
The actual `.env` is gitignored so secrets stay local. If you expose this stack
beyond localhost, change the values in your `.env`.

From repo root:

```bash
pip install -e ".[langfuse]"
```

## Run tests

```bash
cd langfuse
pytest test_questions.py -v
```

Open `http://localhost:3000` to see traces and scores in the Langfuse dashboard.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse server URL |
| `LANGFUSE_PUBLIC_KEY` | `pk-lf-eval-ception` | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | `sk-lf-eval-ception` | Langfuse project secret key |
| `JUDGE_MODEL` | `deepseek-r1:14b` | LLM judge model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |

The default keys match the auto-provisioned project in `docker-compose.yml`.

## Test cases

### Deterministic (pytest assertions)
1. **Who created this website?** - Must contain "Alex" and "Guglielmone"
2. **What tools are open source?** - Must contain "Promptfoo"/"DeepEval", must not contain "Braintrust"/"Langsmith"
3. **Does promptfoo have built-in caching?** - Must start with "yes"
4. **Does deepeval have built-in caching?** - Must start with "no"
5. **Does Ragas have confirmed support for streaming evaluation?** - Must start with "unknown"

### LLM-as-judge (Ollama grader)
6. **What methodology does this website use?** - Evidence tags, proven vs docs
7. **How does it explain evals to different audiences?** - Role-specific explanations

## Teardown

```bash
docker compose -f langfuse/docker-compose.yml down -v
```
