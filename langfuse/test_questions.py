#!/usr/bin/env python3
"""
Langfuse tests for AI Evals website question answering.
https://langfuse.com/docs

Same exam as promptfoo/ and deepeval/ — see docs/simple-exam.md for the spec.
"""

import os
import json

import pytest
import ollama
from langfuse import Langfuse

from eval_ception_core.baseline import ask

# --- Config ---

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-eval-ception")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-eval-ception")
JUDGE_MODEL_NAME = os.getenv("JUDGE_MODEL", "deepseek-r1:14b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# --- Fixtures ---


@pytest.fixture(scope="session")
def langfuse_client():
    return Langfuse(
        host=LANGFUSE_HOST,
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
    )


@pytest.fixture(scope="session")
def judge():
    return ollama.Client(host=OLLAMA_BASE_URL)


# --- Helpers ---


def traced_ask(lf, question, test_name):
    """Ask the agent and record the trace in Langfuse."""
    trace = lf.trace(name=test_name, input=question)
    answer = ask(question)
    trace.update(output=answer)
    lf.flush()
    return answer, trace.id


def llm_judge(judge, question, answer, rubric):
    """Ask an LLM judge: does the answer pass the rubric? Returns (pass/fail, reason)."""
    prompt = (
        "You are a test grader. Decide if the answer passes the rubric.\n\n"
        f"Question: {question}\n\n"
        f"Rubric: {rubric}\n\n"
        f"Answer: {answer}\n\n"
        'Respond with ONLY a JSON object: {"pass": true/false, "reason": "brief reason"}\n'
        "Do not include any other text."
    )
    response = judge.chat(
        model=JUDGE_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.message.content.strip()
    if "</think>" in content:
        content = content.split("</think>")[-1].strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    result = json.loads(content)
    return result["pass"], result.get("reason", "")


def icontains(answer, needle):
    assert needle.lower() in answer.lower(), f"expected '{needle}' in: {answer}"


def not_icontains(answer, needle):
    assert needle.lower() not in answer.lower(), f"unexpected '{needle}' in: {answer}"


def starts_with(answer, token):
    assert answer.lstrip().lower().startswith(token.lower()), (
        f"expected to start with '{token}', got: {answer}"
    )


# --- Deterministic tests (Q1–Q5) ---


def test_website_creator(langfuse_client):
    answer, _ = traced_ask(langfuse_client, "Who created this website?", "Q1-website-creator")
    icontains(answer, "Alex")
    icontains(answer, "Guglielmone")


def test_open_source_frameworks(langfuse_client):
    answer, _ = traced_ask(
        langfuse_client,
        "What tools are open source? (Name all, don't name those that aren't)",
        "Q2-open-source",
    )
    icontains(answer, "Promptfoo")
    icontains(answer, "DeepEval")
    not_icontains(answer, "Braintrust")
    not_icontains(answer, "Langsmith")


def test_promptfoo_caching(langfuse_client):
    answer, _ = traced_ask(
        langfuse_client,
        "Does promptfoo have built-in caching? Start your answer with yes or no.",
        "Q3-promptfoo-caching",
    )
    starts_with(answer, "yes")


def test_deepeval_caching(langfuse_client):
    answer, _ = traced_ask(
        langfuse_client,
        "Does deepeval have built-in caching? Start your answer with yes or no.",
        "Q4-deepeval-caching",
    )
    starts_with(answer, "no")


def test_ragas_streaming(langfuse_client):
    answer, _ = traced_ask(
        langfuse_client,
        "Does Ragas have confirmed support for streaming evaluation? "
        "Start your answer with one of: yes, no, unknown",
        "Q5-ragas-streaming",
    )
    starts_with(answer, "unknown")


# --- LLM-as-judge tests (Q6–Q7) ---


def test_methodology(langfuse_client, judge):
    question = "What methodology does this website use to evaluate tools?"
    rubric = (
        "Pass only if the answer clearly includes ALL of: "
        "1) Evidence-based / hands-on testing methodology. "
        "2) Distinct tags: uppercase = tested/proven, lowercase = docs-only/unverified. "
        "3) Unknown/`?` is used when information is not established. "
        "Fail if any element is missing or the answer invents unsupported details."
    )
    answer, trace_id = traced_ask(langfuse_client, question, "Q6-methodology")
    passed, reason = llm_judge(judge, question, answer, rubric)

    langfuse_client.score(
        name="correctness", value=1 if passed else 0, trace_id=trace_id, comment=reason,
    )
    langfuse_client.flush()

    assert passed, f"LLM judge: FAIL — {reason}"


def test_audience_value(langfuse_client, judge):
    question = "How does this website explain the value of AI evals to different audiences?"
    rubric = (
        "The answer should mention the site tailors explanations to multiple roles. "
        "It should reference at least some of: software engineers (control, move fast "
        "without regressions), product managers (verifiable PoCs, quality over time), "
        "scientists (reduce manual checking, grounded experiments), non-technical "
        "founders (provable, auditable, reduce risk). "
        "Pass if the answer captures that different roles get different value."
    )
    answer, trace_id = traced_ask(langfuse_client, question, "Q7-audience-value")
    passed, reason = llm_judge(judge, question, answer, rubric)

    langfuse_client.score(
        name="correctness", value=1 if passed else 0, trace_id=trace_id, comment=reason,
    )
    langfuse_client.flush()

    assert passed, f"LLM judge: FAIL — {reason}"
