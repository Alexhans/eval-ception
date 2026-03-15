#!/usr/bin/env python3
"""Minimal promptfoo provider: runs Claude CLI with a plugin-dir skill."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

# TODO: Yet another quick wrapper.  Will converge with other options so that there's both pydanticai/strands skill aware options and plaing coding agent (harness) wrappers for the popular ones.
def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not os.getenv("I_KNOW_WHAT_IM_DOING"):
        return {"error": "Set I_KNOW_WHAT_IM_DOING=true to allow Claude CLI to run with file write permissions"}

    config = options.get("config", {}) if isinstance(options, dict) else {}
    raw = config.get("pluginDir", os.getenv("CLAUDE_SKILL_PLUGIN_DIR", os.getenv("BLOG_SAMPLES_DIR", "")))
    plugin_dir = os.path.expandvars(str(raw))

    if not plugin_dir:
        return {"error": "pluginDir config or CLAUDE_SKILL_PLUGIN_DIR env var required"}

    prompt = os.path.expandvars(prompt)

    # Remove stale output so Claude always does a fresh conversion
    vars_ = context.get("vars", {}) if isinstance(context, dict) else {}
    input_file = vars_.get("file", "")
    if input_file:
        output_path = Path(os.path.expandvars(input_file)).with_suffix(".qmd")
        output_path.unlink(missing_ok=True)

    proc = subprocess.run(
        ["claude", "--plugin-dir", plugin_dir, "-p", prompt, "--allowedTools", "Read,Write"],
        capture_output=True, text=True, check=False, cwd=plugin_dir,
        stdin=subprocess.DEVNULL,
    )

    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()}

    # Try to read back the written .qmd file from the `file` var
    vars_ = context.get("vars", {}) if isinstance(context, dict) else {}
    input_file = vars_.get("file", "")
    output = ""
    if input_file:
        output_path = Path(input_file).with_suffix(".qmd")
        if output_path.exists() and output_path.stat().st_mtime > Path(input_file).stat().st_mtime:
            output = output_path.read_text(encoding="utf-8")

    return {"output": output or proc.stdout.strip()}
