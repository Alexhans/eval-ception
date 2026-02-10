from unittest.mock import patch

import grader_provider


@patch("grader_provider.run_grader")
def test_grader_provider_passes_agent_and_model(mock_run_grader):
    mock_run_grader.return_value = {"output": "ok"}

    result = grader_provider.call_api(
        "judge prompt",
        {
            "config": {
                "agent": "claude",
                "model": "sonnet",
                "appendUsageToOutput": False,
                "includeDebugMetrics": True,
            }
        },
        {},
    )

    assert result == {"output": "ok"}
    mock_run_grader.assert_called_once_with(
        "judge prompt",
        agent="claude",
        model="sonnet",
        append_usage_to_output=False,
        include_debug_metrics=True,
        debug=True,
    )
