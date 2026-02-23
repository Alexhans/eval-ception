"""
Adapter: promptfoo results.json -> ai-evals cert JSON.

This module intentionally models an adapter boundary between:
- input: promptfoo result artifacts
- output: ai-evals cert schema artifacts

Usage:
    python -m eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert results.json
    python -m eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert results.json --output cert.json
    python -m eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert results.json --output cert.json --validate path/to/schema.json
"""

import argparse
import json
import sys
import uuid
from datetime import date
from pathlib import Path

# Canonical URL is ai-evals.io/spec/... — will migrate to spec.ai-evals.io once that subdomain has community consensus and stable DNS.
SCHEMA = "https://ai-evals.io/spec/cert/v0.1.0/schema.json"


def infer_check_type(component_results: list) -> str:
    types = {c["assertion"]["type"] for c in component_results}
    if types & {"llm-rubric", "llm-classifier", "model-graded-closedqa"}:
        return "llm-as-judge"
    return "deterministic"


def build_expected(assert_list: list) -> str:
    parts = []
    for a in assert_list:
        t = a["type"]
        v = a.get("value", "")
        if t == "llm-rubric":
            parts.append(f"rubric: {v.strip()}")
        elif t.startswith("not-"):
            parts.append(f"must not contain: {v}")
        else:
            parts.append(str(v))
    return " | ".join(parts)


def _extract_grader_model(first_result: dict) -> str | None:
    provider_cfg = first_result.get("prompt", {}).get("config", {}).get("provider")
    if isinstance(provider_cfg, dict):
        model_name = provider_cfg.get("modelName")
        return str(model_name) if model_name else None
    if isinstance(provider_cfg, str):
        return provider_cfg
    return None


def _extract_question(result_item: dict) -> str:
    vars_ = result_item.get("vars", {})
    if isinstance(vars_, dict):
        for key in ("question", "source", "intent"):
            value = vars_.get(key)
            if isinstance(value, str) and value.strip():
                return value

    test_case_vars = result_item.get("testCase", {}).get("vars", {})
    if isinstance(test_case_vars, dict):
        for key in ("question", "source", "intent"):
            value = test_case_vars.get(key)
            if isinstance(value, str) and value.strip():
                return value

    prompt_raw = result_item.get("prompt", {}).get("raw")
    if isinstance(prompt_raw, str) and prompt_raw.strip():
        return prompt_raw

    return ""


def convert(results_path: Path) -> dict:
    data = json.loads(results_path.read_text())

    results = data["results"]["results"]
    timestamp = data["results"].get("timestamp")
    tags = data.get("config", {}).get("tags", {})
    meta = data.get("metadata", {})
    stats = data["results"].get("stats", {})

    first = results[0] if results else {}
    provider = first.get("provider", {})
    grader_model = _extract_grader_model(first)

    items = []
    for r in results:
        component_results = r["gradingResult"]["componentResults"]
        item = {
            "id": f"Q{r['testIdx'] + 1}",
            "question": _extract_question(r),
            "check_type": infer_check_type(component_results),
            "expected": build_expected(r["testCase"].get("assert", [])),
            "output": r["response"].get("output", ""),
            "score": 1 if r["success"] else 0,
            "passed": r["success"],
            "grader_note": r["gradingResult"]["reason"],
        }
        if r.get("latencyMs") is not None:
            item["latency_ms"] = r["latencyMs"]
        if r.get("response", {}).get("cached") is not None:
            item["cached"] = r["response"]["cached"]
        items.append(item)

    exam = {k: v for k, v in {
        "id": tags.get("exam_id"),
        "version": tags.get("exam_version"),
        "source": tags.get("exam_source"),
    }.items() if v}

    grading_tokens = stats.get("tokenUsage", {}).get("assertions", {}).get("total")

    cert = {
        "$schema": SCHEMA,
        **({"exam": exam} if exam else {}),
        "cert": {
            "id": data.get("evalId", f"CERT-{uuid.uuid4().hex[:8].upper()}"),
            "issued": date.today().isoformat(),
        },
        "agent": {k: v for k, v in {
            "name": provider.get("label"),
        }.items() if v},
        "environment": {k: v for k, v in {
            "evaluated_at": timestamp,
            "framework": "promptfoo",
            "framework_version": meta.get("promptfooVersion"),
            "platform": f"{meta.get('platform', '')}/{meta.get('arch', '')}".strip("/") or None,
            "total_duration_ms": stats.get("durationMs"),
            "grading_tokens": grading_tokens if grading_tokens else None,
        }.items() if v is not None},
        "evaluator": {k: v for k, v in {
            "name": "promptfoo",
            "version": meta.get("promptfooVersion"),
            "grader_model": grader_model,
        }.items() if v},
        "items": items,
    }

    return cert


def main():
    parser = argparse.ArgumentParser(
        description="Adapter: convert promptfoo results.json to ai-evals cert JSON"
    )
    parser.add_argument("input", type=Path, help="Path to promptfoo results.json")
    parser.add_argument("--output", type=Path, default=None, help="Output cert JSON path (default: stdout)")
    parser.add_argument("--validate", type=Path, default=None, metavar="SCHEMA", help="Path to cert JSON schema for validation")
    args = parser.parse_args()

    cert = convert(args.input)

    if args.validate:
        import jsonschema
        schema = json.loads(args.validate.read_text())
        jsonschema.validate(instance=cert, schema=schema)
        print(f"✓ Valid against {args.validate}", file=sys.stderr)

    output_json = json.dumps(cert, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(output_json)
        print(f"Written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
