# Start Here

This repo currently demonstrates one complete path:

`exam config -> promptfoo run -> cert -> viewer`

## 1) Run the canonical exam

From repo root:

```bash
cd exams/airflow-localizer-es
npx promptfoo eval -c promptfooconfig.yaml --filter-providers "^pydantic_skills_ollama$"
```

## 2) Use checked-in cert artifact

Already included from a real run:
- `certs/airflow-localizer-es/airflow-es-localizer-exam-pydantic-agent.cert.json`

If you need to regenerate a cert from your own promptfoo `results.json`, use:

```bash
python -m eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert <path-to-results.json> \
  --output certs/airflow-localizer-es/airflow-es-localizer-exam-pydantic-agent.cert.json
```

## 3) Open in cert viewer

Use your published raw cert URL:

```text
https://<your-viewer-host>/viewer.qmd?cert=<raw-cert-url>
```

Typical raw cert URL pattern (GitHub):

```text
https://raw.githubusercontent.com/<org>/<repo>/<branch>/certs/airflow-localizer-es/airflow-es-localizer-exam-pydantic-agent.cert.json
```

## Repository conventions

- Canonical exam lives under `exams/airflow-localizer-es/`.
- Canonical result artifacts live under `certs/airflow-localizer-es/`.
- Older website/simple-exam artifacts are in `certs/simple-exam/`.
