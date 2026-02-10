from unittest.mock import Mock, patch

import pytest

from eval_ception_core import cli_wrapper_grader as grader_runner


@pytest.fixture(autouse=True)
def _safety_ack_env(monkeypatch):
    monkeypatch.setenv("I_KNOW_WHAT_IM_DOING", "true")


@patch("eval_ception_core.cli_wrapper_grader.subprocess.run")
def test_run_grader_codex_returns_extracted_output(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"text":"ignore"}\n{"output":"grade response"}\n',
        stderr="",
    )

    result = grader_runner.run_grader("grade this")

    assert result == {"output": "grade response"}
    mock_run.assert_called_once_with(
        ["npx", "codex", "exec", "--json", "grade this"],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_grader.subprocess.run")
def test_run_grader_claude_uses_expected_command_and_usage(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout=(
            '{"type":"result","subtype":"success","result":"PASS","usage":{"input_tokens":2,"output_tokens":3}}\n'
        ),
        stderr="",
    )

    result = grader_runner.run_grader("grade this", agent="claude")

    assert result["output"] == "PASS"
    assert result["metadata"] == {
        "usage": {"input_tokens": 2, "output_tokens": 3, "total_tokens": 5}
    }
    mock_run.assert_called_once_with(
        ["claude", "-p", "--output-format", "json", "grade this"],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_grader.subprocess.run")
def test_run_grader_can_append_usage(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"output":"PASS"}\n{"type":"turn.completed","usage":{"input_tokens":4,"output_tokens":6}}\n',
        stderr="",
    )

    result = grader_runner.run_grader("grade", append_usage_to_output=True)
    assert result["output"] == "PASS\n\n[tokens] input=4 output=6 total=10"


def test_run_grader_unsupported_provider():
    result = grader_runner.run_grader("grade", agent="unknown")
    assert result == {"error": "Unsupported agent: unknown"}
