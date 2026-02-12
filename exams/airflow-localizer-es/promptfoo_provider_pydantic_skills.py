#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_PYTHON = os.getenv("PYDANTIC_SKILLS_PYTHON", sys.executable or "python3")


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    config = options.get("config", {}) if isinstance(options, dict) else {}

    provider = str(config.get("provider", "ollama"))
    model = str(config.get("model", "gpt-oss:20b"))
    ollama_base_url = str(config.get("ollamaBaseUrl", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")))
    skills_dir = str(config.get("skillsDir", Path(__file__).with_name(".agents").joinpath("skills")))
    python_bin = str(config.get("pythonBin", os.getenv("PYDANTIC_SKILLS_PYTHON", DEFAULT_PYTHON)))

    script = Path(__file__).with_name("pydantic_agent_with_skills.py")
    cmd = [
        python_bin,
        str(script),
        "--provider",
        provider,
        "--model",
        model,
        "--ollama-base-url",
        ollama_base_url,
        "--skills-dir",
        skills_dir,
        "--json",
        prompt,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()}

    stdout = (proc.stdout or "").strip()
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": f"Failed to parse JSON output from pydantic_agent_with_skills.py: {stdout[:300]}"}

    usage = parsed.get("usage") if isinstance(parsed, dict) else {}
    if not isinstance(usage, dict):
        usage = {}

    result: dict[str, Any] = {"output": str(parsed.get("output", ""))}
    result["metadata"] = {
        "usage": usage,
        "tool_calls": usage.get("tool_calls", 0),
        "messages": parsed.get("messages"),
        "runner": "pydantic_agent_with_skills.py",
    }
    return result
