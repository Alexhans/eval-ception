"""Compatibility wrapper for the core adapter module.

Prefer using:
- python -m eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert
or the installed script entrypoint:
- promptfoo-results-to-ai-evals-cert
"""

from eval_ception_core.adapters.promptfoo_results_to_ai_evals_cert import main


if __name__ == "__main__":
    main()
