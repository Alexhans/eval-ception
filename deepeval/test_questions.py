#!/usr/bin/env python3
"""
DeepEval tests for AI Evals website question answering.
https://docs.confident-ai.com/
"""

import os

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval.models import OllamaModel

from eval_ception_core.baseline import ask

# Judge model (different from the agent model to avoid self-evaluation)
JUDGE_MODEL_NAME = os.getenv("JUDGE_MODEL", "deepseek-r1:14b")
JUDGE_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_answer(question: str) -> str:
    """Get answer from our agent."""
    return ask(question)


def get_judge_model():
    """Create OllamaModel for judging."""
    return OllamaModel(model=JUDGE_MODEL_NAME, base_url=JUDGE_BASE_URL)


def _assert_contains(text: str, needle: str) -> None:
    assert needle.lower() in text.lower(), f"expected to contain '{needle}', got: {text}"


def _assert_not_contains(text: str, needle: str) -> None:
    assert needle.lower() not in text.lower(), f"expected NOT to contain '{needle}', got: {text}"


def _assert_starts_with_token(text: str, token: str) -> None:
    normalized = text.lstrip().lower()
    expected = token.lower()
    assert normalized.startswith(expected), (
        f"expected answer to start with '{token}', got: {text}"
    )


@pytest.fixture
def correctness_metric():
    """GEval metric for answer correctness."""
    return GEval(
        name="Correctness",
        criteria="Determine if the actual output correctly answers the question based on the expected answer.",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
        model=get_judge_model(),
    )


def test_website_creator():
    """Test: Who created this website?"""
    question = "Who created this website?"
    answer = get_answer(question)
    _assert_contains(answer, "Alex")
    _assert_contains(answer, "Guglielmone")


def test_open_source_frameworks():
    """Test: What tools are open source?"""
    question = "What tools are open source? (Name all, don't name those that aren't)"
    answer = get_answer(question)
    _assert_contains(answer, "Promptfoo")
    _assert_contains(answer, "DeepEval")
    _assert_not_contains(answer, "Braintrust")
    _assert_not_contains(answer, "Langsmith")


def test_promptfoo_built_in_caching():
    """Test: Does promptfoo have built-in caching? (deterministic)"""
    question = "Does promptfoo have built-in caching? Start your answer with yes or no."
    answer = get_answer(question)
    _assert_starts_with_token(answer, "yes")


def test_deepeval_built_in_caching():
    """Test: Does deepeval have built-in caching? (deterministic)"""
    question = "Does deepeval have built-in caching? Start your answer with yes or no."
    answer = get_answer(question)
    _assert_starts_with_token(answer, "no")


def test_ragas_streaming_support():
    """Test: Does Ragas have confirmed support for streaming evaluation? (deterministic)"""
    question = (
        "Does Ragas have confirmed support for streaming evaluation? "
        "Start your answer with one of: yes, no, unknown"
    )
    answer = get_answer(question)
    _assert_starts_with_token(answer, "unknown")


def test_methodology(correctness_metric):
    """Test: What methodology does this website use to evaluate tools?"""
    question = "What methodology does this website use to evaluate tools?"
    answer = get_answer(question)

    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output=(
            "The site uses evidence-based evaluation with distinct tags: "
            "'proven' means tested and validated, 'docs' means only mentioned "
            "in documentation but not verified. It prefers marking things as "
            "'unknown' rather than making assumptions. It is based on hands-on "
            "testing, not marketing claims."
        ),
    )
    assert_test(test_case, [correctness_metric])


def test_audience_explanations(correctness_metric):
    """Test: How does this website explain the value of AI evals to different audiences?"""
    question = "How does this website explain the value of AI evals to different audiences?"
    answer = get_answer(question)

    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output=(
            "The site tailors its explanation to multiple roles: software engineers "
            "(control, move fast without regressions), product managers (verifiable "
            "PoCs, quality over time), scientists (reduce manual checking, grounded "
            "experiments), and non-technical founders (provable, auditable, reduce risk)."
        ),
    )
    assert_test(test_case, [correctness_metric])
