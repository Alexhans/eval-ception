#!/usr/bin/env python3
"""
Dangerous CLI wrapper grader for codex/kiro/opencode/claude.

This wrapper is intended for eval workflows where users do not have direct API
access and still want to run model-graded assertions.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from typing import Any

from eval_ception_core.cli_wrapper_agent import (
    _ensure_safety_ack,
    _extract_text_from_parsed,
    _extract_usage_from_parsed,
    _parse_jsonl,
)


def _build_cmd(agent: str, prompt: str, model: str | None = None) -> list[str]:
    agent = agent.lower()
    if agent == "codex":
        cmd = ["npx", "codex", "exec", "--json"]
        if model:
            cmd.extend(["--model", model])
        cmd.append(prompt)
        return cmd
    if agent == "kiro":
        cmd = ["kiro-cli", "chat", "--no-interactive"]
        if model:
            cmd.extend(["--model", model])
        cmd.append(prompt)
        return cmd
    if agent == "opencode-ai":
        cmd = ["npx", "opencode-ai", "run"]
        if model:
            cmd.extend(["--model", model])
        cmd.append(prompt)
        return cmd
    if agent == "claude":
        cmd = ["claude", "-p", "--output-format", "json", prompt]
        if model:
            cmd.extend(["--model", model])
        return cmd
    raise ValueError(f"Unsupported agent: {agent}")


def run_grader(
    prompt: str,
    agent: str = "codex",
    model: str | None = None,
    append_usage_to_output: bool = False,
    include_debug_metrics: bool = True,
    debug: bool = False,
) -> dict[str, Any]:
    debug = debug or os.getenv("CLI_WRAPPER_GRADER_DEBUG", "").strip() == "1"

    safety_error = _ensure_safety_ack()
    if safety_error:
        return {"error": safety_error}

    try:
        cmd = _build_cmd(agent, prompt, model=model)
    except ValueError as exc:
        return {"error": str(exc)}

    if debug:
        print(
            f"[cli_wrapper_grader:debug] agent={agent} model={model or '<default>'}",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"[cli_wrapper_grader:debug] cmd={shlex.join(cmd)}",
            file=sys.stderr,
            flush=True,
        )

    try:
        if not debug:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            returncode = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        else:
            popen = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout_chunks: list[str] = []
            stderr_chunks: list[str] = []

            def _pump(pipe, chunks: list[str], label: str) -> None:
                if pipe is None:
                    return
                for line in pipe:
                    chunks.append(line)
                    print(
                        f"[cli_wrapper_grader:{label}] {line.rstrip()}",
                        file=sys.stderr,
                        flush=True,
                    )

            t_out = threading.Thread(target=_pump, args=(popen.stdout, stdout_chunks, "stdout"), daemon=True)
            t_err = threading.Thread(target=_pump, args=(popen.stderr, stderr_chunks, "stderr"), daemon=True)
            t_out.start()
            t_err.start()
            returncode = popen.wait()
            t_out.join()
            t_err.join()
            stdout = "".join(stdout_chunks)
            stderr = "".join(stderr_chunks)
            print(
                f"[cli_wrapper_grader:debug] exit_code={returncode}",
                file=sys.stderr,
                flush=True,
            )
    except Exception as exc:
        return {"error": str(exc)}

    if returncode != 0:
        stderr = (stderr or "").strip()
        stdout = (stdout or "").strip()
        return {"error": stderr or stdout or f"CLI command failed with exit code {returncode}"}

    parsed = _parse_jsonl(stdout or "")
    output = _extract_text_from_parsed(parsed, stdout or "")
    usage = _extract_usage_from_parsed(parsed)

    if append_usage_to_output and usage:
        output = (
            f"{output}\n\n"
            f"[tokens] input={usage.get('input_tokens')} "
            f"output={usage.get('output_tokens')} "
            f"total={usage.get('total_tokens')}"
        )

    result: dict[str, Any] = {"output": output}
    if include_debug_metrics and usage:
        result["metadata"] = {"usage": usage}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dangerous CLI wrapper grader for eval workflows. "
            "Use only in controlled environments."
        ),
        epilog=(
            "Requires I_KNOW_WHAT_IM_DOING=true. This wrapper executes external CLI agents "
            "for grading prompts and may inherit tool/network permissions."
        ),
    )
    parser.add_argument("prompt", nargs="+", help="Prompt text sent to the grader model")
    parser.add_argument(
        "--agent",
        "--cli-agent-provider",
        dest="agent",
        default="codex",
        choices=("codex", "kiro", "opencode-ai", "claude"),
        help="CLI backend used for grading prompts",
    )
    parser.add_argument(
        "--model",
        help="Optional model name passed through to the selected CLI backend",
    )
    parser.add_argument(
        "--usage",
        "--append-usage-to-output",
        action="store_true",
        dest="append_usage_to_output",
        help="Append token usage line to output when available",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show progress logs to stderr while the command runs.",
    )
    parser.add_argument(
        "--no-debug-metrics",
        action="store_true",
        help="Do not include usage metadata in JSON output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON result instead of output text only.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress logs even when --verbose or --debug is enabled.",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help=(
            "Enable detailed stderr debug logs (command + live subprocess output). "
            "Implies --verbose."
        ),
    )
    args = parser.parse_args()

    stop_event = threading.Event()
    heartbeat_thread: threading.Thread | None = None
    started_at = time.monotonic()
    progress_enabled = (args.verbose or args.debug) and not args.no_progress
    if progress_enabled:
        print(
            f"[cli_wrapper_grader] starting agent={args.agent}",
            file=sys.stderr,
            flush=True,
        )

        def _heartbeat() -> None:
            while not stop_event.wait(5):
                elapsed = int(time.monotonic() - started_at)
                print(
                    f"[cli_wrapper_grader] still running ({elapsed}s elapsed)",
                    file=sys.stderr,
                    flush=True,
                )

        heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
        heartbeat_thread.start()

    result = run_grader(
        " ".join(args.prompt),
        agent=args.agent,
        model=args.model,
        append_usage_to_output=args.append_usage_to_output,
        include_debug_metrics=not args.no_debug_metrics,
        debug=args.debug,
    )
    stop_event.set()
    if heartbeat_thread is not None:
        heartbeat_thread.join()
    if progress_enabled:
        elapsed = int(time.monotonic() - started_at)
        print(
            f"[cli_wrapper_grader] completed in {elapsed}s",
            file=sys.stderr,
            flush=True,
        )

    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=True))
    else:
        print(result.get("output", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
