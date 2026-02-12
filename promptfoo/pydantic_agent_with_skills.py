#!/usr/bin/env python3
import asyncio
import argparse
import json
import logging
import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai_skills import SkillsToolset

DEFAULT_BEDROCK_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def _usage_to_dict(usage_obj) -> dict:
    if usage_obj is None:
        return {}
    if hasattr(usage_obj, "model_dump"):
        data = usage_obj.model_dump()
        if isinstance(data, dict):
            return data
    if hasattr(usage_obj, "dict"):
        data = usage_obj.dict()
        if isinstance(data, dict):
            return data
    out = {}
    for key in ("input_tokens", "output_tokens", "requests", "tool_calls"):
        if hasattr(usage_obj, key):
            out[key] = getattr(usage_obj, key)
    return out


async def run(
    agent: Agent,
    prompt: str,
    auto: bool = True,
    verbose: bool = False,
    emit_output: bool = True,
):
    messages = []
    last_result = None
    
    while True:
        result = await agent.run(prompt, message_history=messages)
        last_result = result
        messages = result.all_messages()
        
        if verbose:
            print("\n=== RESULT ===")
            print(f"Output: {result.output}")
            print(f"All messages: {len(messages)} messages")
            print(f"Usage: {result.usage()}")
            print("=============\n")
        
        if emit_output:
            print(result.output)
        
        if auto or not isinstance(result.output, str):
            break
        
        user_input = input("\n> ").strip()
        if not user_input:
            break
        prompt = user_input

    if last_result is None:
        return {"output": "", "usage": {}, "messages": len(messages)}

    return {
        "output": str(last_result.output),
        "usage": _usage_to_dict(last_result.usage()),
        "messages": len(messages),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="Hello")
    parser.add_argument(
        "--provider",
        choices=("bedrock", "ollama"),
        default="bedrock",
        help="Model backend provider",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name/id for the selected provider",
    )
    parser.add_argument(
        "--ollama-base-url",
        default=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        help="Base URL for Ollama (used when --provider ollama)",
    )
    parser.add_argument(
        "--skills-dir",
        default=str(Path(__file__).resolve().parent / ".agents" / "skills"),
        help="Directory containing SKILL.md folders",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print structured JSON result")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.provider == "bedrock":
        from pydantic_ai.models.bedrock import BedrockConverseModel
        from pydantic_ai.providers.bedrock import BedrockProvider

        effective_model = args.model or DEFAULT_BEDROCK_MODEL
        provider = BedrockProvider(region_name="us-east-1")
        model = BedrockConverseModel(effective_model, provider=provider)
    else:
        # PydanticAI resolves provider-prefixed model strings.
        # Example effective model: ollama:gpt-oss:20b
        effective_model = args.model or DEFAULT_OLLAMA_MODEL
        os.environ["OLLAMA_BASE_URL"] = args.ollama_base_url
        model = effective_model if effective_model.startswith("ollama:") else f"ollama:{effective_model}"
    
    skills = SkillsToolset(directories=[args.skills_dir])
    agent = Agent(model, toolsets=[skills])

    if args.verbose:
        print(f"Using provider: {args.provider}")
        print(f"Using model: {effective_model}")
        if args.provider == "ollama":
            print(f"Using OLLAMA_BASE_URL: {os.environ.get('OLLAMA_BASE_URL')}")
        print(f"Loaded skills from: {args.skills_dir}")

    result = asyncio.run(
        run(
            agent,
            args.prompt,
            auto=not args.interactive,
            verbose=args.verbose,
            emit_output=not args.json,
        )
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
