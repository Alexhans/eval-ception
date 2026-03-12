

# Airflow Localizer (Spanish) Exam

Real example of how to evaluate an AI agent skill using the exam/cert pattern. The domain is Spanish localization of the Airflow UI, based on a real open contribution:

- [Mailing list](https://www.mail-archive.com/commits%40airflow.apache.org/msg492611.html)
- [GitHub issue](https://github.com/apache/airflow/issues/61984#issuecomment-3928108863)
- [Spanish Localization](https://github.com/apache/airflow/issues/61991)

An exam such as this would be enough to confirm some characteristics of what is good enough, regardless of the actual caller of the skills (OpenCode/Codex/PydanticAI with Skills custom agent) and model (GLM-5 cloud, Opus, gpt-oss:20b).

One could even iterate on the skills themselves, making them smaller or more deterministic to reduce token count.

## Skill setup

This exam expects the `airflow-translations` skill to be discoverable.

Two valid options:
- Create `exams/airflow-localizer-es/.agents/skills/airflow-translations` (for example via symlink to Airflow's `.github/skills/airflow-translations`).
- Or set `skillsDir` in `promptfooconfig.yaml` explicitly for your environment.

## How to run

Run from this exam directory so local runner files resolve cleanly:

```bash
cd exams/airflow-localizer-es
npx promptfoo eval -c promptfooconfig.yaml --filter-providers '^pydantic_skills_ollama$'
```

## View it with AI Evals Cert Viewer

- https://ai-evals.io/certify-your-agent/viewer.html?cert=https://raw.githubusercontent.com/Alexhans/eval-ception/main/certs/airflow-localizer-es/airflow-es-localizer-exam-pydantic-agent.cert.json