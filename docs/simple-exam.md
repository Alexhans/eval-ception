# Simple Exam Model

This repository is centered on one idea: an agent must pass a qualification exam before it can represent your domain.

The question set is intentionally simple and small to be easy to understand.  It contains questions and verifications that you might disagree with and that's the point. How would you make it better? How would you make your own?  Intentionality matters when making an exam.  Real life exams often have the problem where human graders haven't actually gone through the exams and then get unexpected results from the takers.

| Component | Meaning |
|---|---|
| Question | What you ask about your domain/site/product |
| Agent | Any system that answers the question (local model, CLI agent, custom endpoint) |
| Assertion | How correctness is checked (deterministic or LLM-as-judge) |
| Exam | The set of questions + assertions used as a qualification gate |
| tool folder | A specific implementation of the same exam idea (`promptfoo/`, `deepeval/`, `langfuse/`) |

## Why This Matters

Each eval tool folder in this repo applies the same exam concept with different tooling mechanics.
It is not a different domain or a different objective per folder.

## Source Of Truth

There is no single shared exam file across all tools in this repository.
The source of truth is conceptual: same domain intent + equivalent questions/assertions,
implemented per tool.

We break the DRY (Don't repeat yourself) principle for the sake of clarity of self-contained examples.

This might change if it becomes unwieldy.

## Canonical Question Set (v1)

Use these exact phrasings when possible so tool outputs are comparable.

| ID | Question (canonical wording) | Check type intent |
|---|---|---|
| Q1 | Who created this website? | Deterministic |
| Q2 | What tools are open source? (Name all, don't name those that aren't) | Deterministic |
| Q3 | Does promptfoo have built-in caching? Start your answer with yes or no. | Deterministic |
| Q4 | Does deepeval have built-in caching? Start your answer with yes or no. | Deterministic |
| Q5 | Does Ragas have confirmed support for streaming evaluation? Start your answer with one of: yes, no, unknown | Deterministic (hallucination probe) |
| Q6 | What methodology does this website use to evaluate tools? | LLM-as-judge |
| Q7 | How does this website explain the value of AI evals to different audiences? | LLM-as-judge |

Notes:
- "this website" is intentional and tests contextual grounding from setup/system context.
- Q3/Q4/Q5 are intentionally shaped for cheap deterministic checks (starts-with style answers).
- If deterministic shape cannot be enforced for a question, use LLM-as-judge (Trading off cost/speed).

## tool Map (Exam + Data)

| tool | Run Guide | Exam Definition | Result/Data Location |
|---|---|---|---|
| Promptfoo | [`promptfoo/README.md`](../promptfoo/README.md) | [`promptfoo/promptfooconfig.yaml`](../promptfoo/promptfooconfig.yaml) | Promptfoo local eval store (`.promptfoo/`) + `promptfoo view` |
| DeepEval | [`deepeval/README.md`](../deepeval/README.md) | [`deepeval/test_questions.py`](../deepeval/test_questions.py) | Pytest output (terminal/CI) |
| Langfuse | [`langfuse/README.md`](../langfuse/README.md) | [`langfuse/test_questions.py`](../langfuse/test_questions.py) | Pytest output + Langfuse dashboard (`localhost:3000`) |
