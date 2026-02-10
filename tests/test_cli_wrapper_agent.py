from unittest.mock import Mock, patch

import pytest

from eval_ception_core import cli_wrapper_agent as agent_runner


@pytest.fixture(autouse=True)
def _safety_ack_env(monkeypatch):
    monkeypatch.setenv("I_KNOW_WHAT_IM_DOING", "true")


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_codex_returns_extracted_output(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"text":"ignore"}\n{"output":"final answer"}\n',
        stderr="",
    )

    result = agent_runner.run_agent(
        "Hello",
        agent="codex",
    )

    assert result == {"output": "final answer"}
    mock_run.assert_called_once_with(
        [
            "npx",
            "codex",
            "exec",
            "--json",
            agent_runner._compose_user_prompt("Hello"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_opencode_ai_uses_expected_command(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout="final answer",
        stderr="",
    )

    result = agent_runner.run_agent("Who owns ai-evals.io?", agent="opencode-ai")

    assert result == {"output": "final answer"}
    mock_run.assert_called_once_with(
        [
            "npx",
            "opencode-ai",
            "run",
            agent_runner._compose_user_prompt("Who owns ai-evals.io?"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_codex_can_set_model(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout="final answer",
        stderr="",
    )

    result = agent_runner.run_agent("Hello", agent="codex", model="mini")
    assert result == {"output": "final answer"}
    mock_run.assert_called_once_with(
        [
            "npx",
            "codex",
            "exec",
            "--json",
            "--model",
            "mini",
            agent_runner._compose_user_prompt("Hello"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_claude_uses_expected_command_and_extracts_json_result(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout=(
            '{"type":"result","subtype":"success","result":"Hello!","total_cost_usd":0.0406105,'
            '"usage":{"input_tokens":3,"output_tokens":12}}\n'
        ),
        stderr="",
    )

    result = agent_runner.run_agent("hello", agent="claude")

    assert result["output"] == "Hello!"
    assert result["metadata"] == {
        "usage": {"input_tokens": 3, "output_tokens": 12, "total_tokens": 15}
    }
    mock_run.assert_called_once_with(
        [
            "claude",
            "-p",
            "--output-format",
            "json",
            "hello",
            "--system-prompt",
            agent_runner.DEFAULT_SYSTEM_PROMPT,
            "--tools",
            "WebSearch,WebFetch",
            "--permission-mode",
            "bypassPermissions",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_codex_jsonl_extracts_penultimate_agent_message(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout=(
            '{"type":"thread.started","thread_id":"abc"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"item.completed","item":{"id":"item_9","type":"agent_message","text":"This website was created by Alex Guglielmone."}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}\n'
        ),
        stderr="",
    )

    result = agent_runner.run_agent(
        "Who created this website?",
        agent="codex",
    )

    assert result == {
        "output": "This website was created by Alex Guglielmone.",
        "metadata": {"usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}},
    }


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_codex_can_append_usage_to_output(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout=(
            '{"type":"item.completed","item":{"type":"agent_message","text":"Answer text"}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":7,"output_tokens":3}}\n'
        ),
        stderr="",
    )

    result = agent_runner.run_agent(
        "Q", agent="codex", append_usage_to_output=True
    )

    assert result["output"] == "Answer text\n\n[tokens] input=7 output=3 total=10"
    assert result["metadata"] == {"usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}}


@patch("eval_ception_core.cli_wrapper_agent.subprocess.run")
def test_run_agent_plain_text_returns_last_non_empty_line(mock_run):
    mock_run.return_value = Mock(
        returncode=0,
        stdout=(
            "> build - thing\n"
            "tool logs\n"
            "\n"
            "Alex Guglielmone Nemi owns ai-evals.io.\n"
        ),
        stderr="",
    )

    result = agent_runner.run_agent("Q", agent="opencode-ai")
    assert result == {"output": "Alex Guglielmone Nemi owns ai-evals.io."}


def test_run_agent_unsupported_provider():
    result = agent_runner.run_agent("Q", agent="unknown")
    assert result == {"error": "Unsupported agent: unknown"}
