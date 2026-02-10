#!/usr/bin/env python3
"""
Promptfoo provider that wraps our agent.
https://www.promptfoo.dev/docs/providers/python/
"""

from eval_ception_core.baseline import ask


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """
    Promptfoo provider interface.

    Args:
        prompt: The rendered prompt (our question)
        options: Provider options from config
        context: Test context including vars

    Returns:
        dict with 'output' key containing the answer
    """
    try:
        answer = ask(prompt)
        return {"output": answer}
    except Exception as e:
        return {"error": str(e)}
