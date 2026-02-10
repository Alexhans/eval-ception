#!/usr/bin/env python3
"""
Illustrative baseline agent for eval-ception.

By default it targets ai-evals.io, but you can override the URL.
This sample is framework-agnostic (not tied to any specific agent framework).
It uses Ollama for simplicity (powered by llama.cpp).
"""

import argparse
import json
import logging
import os
import re
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright
import ollama

DEFAULT_BASE_URL = "https://ai-evals.io"
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_MAX_PAGES = 10
OLLAMA_HELP = (
    "This baseline agent requires Ollama. It usually runs at http://localhost:11434. "
    "See https://ollama.com and https://github.com/ggml-org/llama.cpp ."
)

logger = logging.getLogger(__name__)


def setup_logging(level: str = None):
    """Configure logging based on level string or LOG_LEVEL env var."""
    level = level or os.getenv("LOG_LEVEL", "WARNING")
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def extract_links(page, base_url: str) -> list[str]:
    """Extract all same-domain links from a page."""
    base_domain = urlparse(base_url).netloc
    links = []

    for anchor in page.query_selector_all("a[href]"):
        href = anchor.get_attribute("href")
        if not href:
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only keep same-domain links, skip anchors and non-http
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            # Normalize: remove fragment, trailing slash
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            clean_url = clean_url.rstrip("/")
            if clean_url and clean_url not in links:
                links.append(clean_url)

    return links


def fetch_page(page, url: str) -> tuple[str, list[str]]:
    """Fetch a page and return (content, links)."""
    logger.info(f"Fetching: {url}")
    page.goto(url, wait_until="networkidle")
    content = page.inner_text("body")
    links = extract_links(page, url)
    logger.info(f"Got {len(content)} chars, {len(links)} links")
    logger.debug(f"Content:\n{content[:500]}...")
    return content, links


def ask_llm_decision(question: str, pages_visited: dict, available_links: list[str], model: str) -> dict:
    """Ask LLM whether to continue researching or answer."""

    # Build context from visited pages
    context_parts = []
    for url, content in pages_visited.items():
        context_parts.append(f"=== {url} ===\n{content}\n")
    context = "\n".join(context_parts)

    prompt = f"""You are a research agent. Your task is to answer a question about a website.

QUESTION: {question}

PAGES YOU HAVE VISITED:
{context}

AVAILABLE LINKS TO EXPLORE (not yet visited):
{json.dumps(available_links, indent=2)}

Based on the content you've gathered, decide:
1. If you have enough information to answer the question confidently, respond with:
   {{"action": "answer", "answer": "your answer here"}}

2. If you need more information, pick a link to visit next:
   {{"action": "visit", "url": "url to visit"}}

Respond with ONLY valid JSON, no other text."""

    logger.debug(f"Decision prompt:\n{prompt}")

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise RuntimeError(f"{OLLAMA_HELP} Original error: {e}") from e

    raw = response["message"]["content"]
    logger.debug(f"LLM raw response:\n{raw}")

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: treat whole response as answer
    logger.warning("Could not parse LLM response as JSON, treating as answer")
    return {"action": "answer", "answer": raw}


def ask(question: str, base_url: str = None, model: str = None, max_pages: int = None) -> str:
    """
    Main entry point: crawl website and answer question.

    Uses an agentic loop where the LLM decides when to stop researching.
    """
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise RuntimeError("Refusing to run as root. Run as a non-root user with Chromium sandbox enabled.")

    base_url = base_url or os.getenv("BASE_URL", DEFAULT_BASE_URL)
    model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    max_pages = max_pages or int(os.getenv("MAX_PAGES", DEFAULT_MAX_PAGES))

    # Normalize base URL
    base_url = base_url.rstrip("/")

    logger.info(f"Question: {question}")
    logger.info(f"Starting at: {base_url}")
    logger.info(f"Max pages: {max_pages}")

    pages_visited = {}
    available_links = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Fetch starting page
            content, links = fetch_page(page, base_url)
            pages_visited[base_url] = content
            available_links.update(links)

            # Agentic loop
            while len(pages_visited) < max_pages:
                # Remove already visited from available
                remaining_links = [l for l in available_links if l not in pages_visited]

                logger.info(f"Visited {len(pages_visited)} pages, {len(remaining_links)} links available")

                # Ask LLM what to do
                decision = ask_llm_decision(question, pages_visited, remaining_links, model)
                logger.info(f"LLM decision: {decision.get('action')}")

                if decision.get("action") == "answer":
                    browser.close()
                    answer = decision.get("answer", "")
                    logger.debug(f"Final answer:\n{answer}")
                    return answer

                elif decision.get("action") == "visit":
                    url_to_visit = decision.get("url", "")
                    if url_to_visit and url_to_visit not in pages_visited:
                        try:
                            content, links = fetch_page(page, url_to_visit)
                            pages_visited[url_to_visit] = content
                            available_links.update(links)
                        except Exception as e:
                            logger.warning(f"Failed to fetch {url_to_visit}: {e}")
                            pages_visited[url_to_visit] = f"[Error fetching page: {e}]"
                    else:
                        logger.warning(f"Invalid or already visited URL: {url_to_visit}")
                        # If LLM keeps suggesting invalid URLs, force an answer
                        if not remaining_links:
                            break
                else:
                    logger.warning(f"Unknown action: {decision}")
                    break

            browser.close()
    except Exception as e:
        raise RuntimeError(
            "Baseline agent failed. Check that Playwright is installed and Ollama is running. "
            f"Original error: {e}"
        ) from e


    # Exhausted max pages or links - force final answer
    logger.info("Max pages reached or no more links, forcing final answer")
    final_prompt = f"""Based on all the website content you've gathered, answer this question:

QUESTION: {question}

CONTENT GATHERED:
{chr(10).join(f'=== {url} ==={chr(10)}{content}' for url, content in pages_visited.items())}

Answer concisely and directly."""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": final_prompt}],
        )
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"{OLLAMA_HELP} Original error: {e}") from e


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Illustrative baseline agent for ai-evals.io (default). "
            "Framework-agnostic sample for eval workflows. "
            "Uses Ollama for simplicity (powered by llama.cpp)."
        ),
        epilog=(
            "Default target is ai-evals.io. Override with --url if needed. "
            "Security: run as non-root and keep Chromium sandbox enabled. "
            "Do not use --no-sandbox."
        ),
    )
    parser.add_argument("question", help="The question to ask")
    parser.add_argument("--url", "-u", help=f"Website URL override (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--model", "-m", help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-pages", "-p", type=int, help=f"Max pages to crawl (default: {DEFAULT_MAX_PAGES})")
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "WARNING"),
        help="Logging level (default: WARNING, or LOG_LEVEL env var)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Shortcut for --log-level INFO")

    args = parser.parse_args()

    # Determine log level
    if args.verbose:
        log_level = "INFO"
    else:
        log_level = args.log_level

    setup_logging(log_level)

    try:
        answer = ask(args.question, base_url=args.url, model=args.model, max_pages=args.max_pages)
        print(answer)
    except Exception as e:
        logger.error(str(e))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
