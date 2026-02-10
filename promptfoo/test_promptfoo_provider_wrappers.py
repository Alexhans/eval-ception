from unittest.mock import patch

import promptfoo_provider_claude as provider_claude
import promptfoo_provider_codex as provider_codex
import promptfoo_provider_opencode as provider_opencode


@patch("promptfoo_provider_codex.run_agent")
def test_codex_provider_passes_model(mock_run_agent):
    mock_run_agent.return_value = {"output": "ok"}

    result = provider_codex.call_api(
        "q",
        {"config": {"model": "mini", "appendUsageToOutput": False, "includeDebugMetrics": True}},
        {},
    )

    assert result == {"output": "ok"}
    mock_run_agent.assert_called_once_with(
        "q",
        agent="codex",
        model="mini",
        append_usage_to_output=False,
        include_debug_metrics=True,
        debug=True,
    )


@patch("promptfoo_provider_claude.run_agent")
def test_claude_provider_passes_model(mock_run_agent):
    mock_run_agent.return_value = {"output": "ok"}

    result = provider_claude.call_api(
        "q",
        {"config": {"model": "sonnet", "appendUsageToOutput": True, "includeDebugMetrics": False}},
        {},
    )

    assert result == {"output": "ok"}
    mock_run_agent.assert_called_once_with(
        "q",
        agent="claude",
        model="sonnet",
        append_usage_to_output=True,
        include_debug_metrics=False,
        debug=True,
    )


@patch("promptfoo_provider_opencode.run_agent")
def test_opencode_provider_passes_model(mock_run_agent):
    mock_run_agent.return_value = {"output": "ok"}

    result = provider_opencode.call_api(
        "q",
        {"config": {"model": "fast", "appendUsageToOutput": True, "includeDebugMetrics": True}},
        {},
    )

    assert result == {"output": "ok"}
    mock_run_agent.assert_called_once_with(
        "q",
        agent="opencode-ai",
        model="fast",
        append_usage_to_output=True,
        include_debug_metrics=True,
        debug=True,
    )
