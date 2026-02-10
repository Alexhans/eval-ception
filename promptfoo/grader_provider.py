#!/usr/bin/env python3
"""
Promptfoo grader provider backed by wrapped-cli-grader.

Use this when users do not have direct API access for --grader and want to
grade via a local CLI agent (codex/claude/opencode).
"""

from __future__ import annotations

from typing import Any

import os

from eval_ception_core.cli_wrapper_grader import run_grader


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    config = options.get("config", {}) if isinstance(options, dict) else {}
    agent = str(config.get("agent", os.getenv("CLI_GRADER_AGENT", "codex")))
    model = config.get("model")
    debug = bool(config.get("debug", True))
    include_debug_metrics = bool(config.get("includeDebugMetrics", True))
    append_usage_to_output = bool(config.get("appendUsageToOutput", False))
    return run_grader(
        prompt,
        agent=agent,
        model=str(model) if model is not None else None,
        append_usage_to_output=append_usage_to_output,
        include_debug_metrics=include_debug_metrics,
        debug=debug,
    )
