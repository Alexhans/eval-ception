# Eval-ception

Quickly test the evals concept against `ai-evals.io` (as shown in the tutorial):
https://ai-evals.io/cookbook/eval-ception.html

## What this repo is for

Run a qualification exam for an agent that answers questions about your domain.

## What The Exam Is

See [`docs/simple-exam.md`](docs/simple-exam.md) for the exam model, source-of-truth rules,
and direct links to each framework's exam/data files.
Short version: each framework folder (`promptfoo/`, `deepeval/`, `langfuse/`)
implements the same exam idea with different tooling mechanics.

## Agent paths

1. Custom provider (recommended default)
2. CLI wrappers (`codex`, `claude`, `opencode_ai`)
3. Local model (`ollama_agent`) via baseline Playwright + Ollama agent

## Choose your path

- Custom provider: start in `promptfoo/README.md`, then implement `call_api(...)`
  in `promptfoo/ollama_provider.py` (wired as `ollama_agent` label in this starter config).
  First run:
  `cd promptfoo && npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^ollama_agent$" -n 1 --verbose`
- CLI wrappers (`codex`/`claude`/`opencode_ai`): start in `promptfoo/README.md`.
  First run:
  `cd promptfoo && npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^codex$" -n 1 --verbose`
- Local model (`ollama_agent`): install models below, then run:
  `cd promptfoo && npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^ollama_agent$" -n 1 --verbose`

## Quick start (local model path)

```bash
git clone https://github.com/Alexhans/eval-ception
cd eval-ception

# shared core package (installs baseline-agent CLI)
pip install -e .

# local models
ollama pull qwen3:8b
ollama pull deepseek-r1:14b
```

Defaults above match this repo's tested setup (`qwen3:8b` for agent, `deepseek-r1:14b` for grader).
They do not need to be different models; using the same model for both is valid.

## Install by tool

```bash
# Promptfoo path (Node-based; no extra Python deps required beyond base)
pip install -e .

# DeepEval path
pip install -e ".[deepeval]"

# Langfuse path
pip install -e ".[langfuse]"
```

### Optional: test baseline agent standalone first

```bash
baseline-agent --log-level DEBUG "Who created the website ai-evals.io?"
```

`-v` is a shortcut for `INFO`. Use `--log-level DEBUG` for debug output.

### Optional: test wrapped CLI agent standalone

```bash
export I_KNOW_WHAT_IM_DOING=true
wrapped-cli-agent --agent codex --url https://ai-evals.io/ --usage --json "What is this site about?"
```

### Optional: test wrapped CLI grader standalone

```bash
export I_KNOW_WHAT_IM_DOING=true
wrapped-cli-grader --agent codex --json "Return PASS if the answer satisfies the rubric."
```

Localhost testing example:

```bash
export I_KNOW_WHAT_IM_DOING=true
wrapped-cli-agent --agent codex --url http://127.0.0.1:1234 --json "What is this site about?"
```

If you want to test against a local copy of the site, clone and serve:

```bash
git clone https://github.com/Alexhans/ai-evals
cd ai-evals/evals_site/_site
python -m http.server 1234
```

Security notes for wrapped CLI agent:
- Requires explicit opt-in: `I_KNOW_WHAT_IM_DOING=true`
- Executes external CLI agents and may grant tool/network permissions depending on those CLIs
- Intended for controlled environments; for safer local baseline use `baseline-agent`
- Hardening roadmap: sandbox profiles (`strace` / `bwrap`)

## Eval tool guides

For framework-specific commands and options:

- Promptfoo: [`promptfoo/README.md`](promptfoo/README.md)
- DeepEval: [`deepeval/README.md`](deepeval/README.md)
- Langfuse: [`langfuse/README.md`](langfuse/README.md)

Promptfoo includes smoke/full exam commands, provider filtering, and grader options
(Ollama, OpenAI-compatible URL, and CLI-wrapper grader).
