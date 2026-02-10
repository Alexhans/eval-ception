#!/usr/bin/env python3
"""
Promptfoo provider for the OpenCode CLI runner.
"""

from __future__ import annotations

from typing import Any

from eval_ception_core.cli_wrapper_agent import run_agent


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    config = options.get("config", {}) if isinstance(options, dict) else {}
    model = config.get("model")
    debug = bool(config.get("debug", True))
    include_debug_metrics = bool(config.get("includeDebugMetrics", True))
    append_usage_to_output = bool(config.get("appendUsageToOutput", True))
    return run_agent(
        prompt,
        agent="opencode-ai",
        model=str(model) if model is not None else None,
        append_usage_to_output=append_usage_to_output,
        include_debug_metrics=include_debug_metrics,
        debug=debug,
    )
