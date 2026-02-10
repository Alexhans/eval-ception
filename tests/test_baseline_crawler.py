from __future__ import annotations

from dataclasses import dataclass

import pytest

from eval_ception_core.baseline import crawler


@dataclass
class _Anchor:
    href: str | None

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self.href
        return None


class _FakePageForLinks:
    def __init__(self, hrefs: list[str | None]):
        self._hrefs = hrefs

    def query_selector_all(self, selector: str):
        assert selector == "a[href]"
        return [_Anchor(h) for h in self._hrefs]


class _FakePage:
    pass


class _FakeBrowser:
    def new_page(self):
        return _FakePage()

    def close(self):
        return None


class _FakeChromium:
    def launch(self, headless: bool = True):
        return _FakeBrowser()


class _FakePlaywrightCtx:
    def __enter__(self):
        class _P:
            chromium = _FakeChromium()

        return _P()

    def __exit__(self, exc_type, exc, tb):
        return False


def _patch_playwright(monkeypatch):
    monkeypatch.setattr(crawler, "sync_playwright", lambda: _FakePlaywrightCtx())


def test_extract_links_excludes_external_links():
    page = _FakePageForLinks(
        [
            "/about",
            "https://ai-evals.io/cookbook/",
            "https://google.com",
            "mailto:test@example.com",
            "#section",
            None,
        ]
    )

    links = crawler.extract_links(page, "https://ai-evals.io")

    assert "https://ai-evals.io/about" in links
    assert "https://ai-evals.io/cookbook" in links
    assert all("google.com" not in link for link in links)
    assert all(not link.startswith("mailto:") for link in links)


def test_ask_handles_invalid_or_already_visited_url(monkeypatch):
    _patch_playwright(monkeypatch)

    calls = {"n": 0}

    def fake_fetch_page(page, url):
        return "home", ["https://ai-evals.io/about"]

    def fake_decision(question, pages_visited, available_links, model):
        calls["n"] += 1
        if calls["n"] == 1:
            # Already visited URL should be handled safely.
            return {"action": "visit", "url": "https://ai-evals.io"}
        return {"action": "answer", "answer": "Alex Guglielmone Nemi"}

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)
    monkeypatch.setattr(crawler, "ask_llm_decision", fake_decision)

    answer = crawler.ask(
        "Who created this website?",
        base_url="https://ai-evals.io",
        model="qwen3:8b",
        max_pages=3,
    )

    assert "Alex" in answer
    assert calls["n"] == 2


def test_ask_reaches_max_pages_and_uses_forced_final_answer(monkeypatch):
    _patch_playwright(monkeypatch)

    def fake_fetch_page(page, url):
        return "home", []

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)

    captured = {"prompt": ""}

    def fake_ollama_chat(*, model, messages):
        captured["prompt"] = messages[0]["content"]
        return {"message": {"content": "Final fallback answer"}}

    monkeypatch.setattr(crawler.ollama, "chat", fake_ollama_chat)

    answer = crawler.ask(
        "Who created this website?",
        base_url="https://ai-evals.io",
        model="qwen3:8b",
        max_pages=1,
    )

    assert answer == "Final fallback answer"
    assert "Based on all the website content you've gathered" in captured["prompt"]


def test_ask_llm_decision_shows_ollama_help_on_connection_failure(monkeypatch):
    def fake_chat(*, model, messages):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(crawler.ollama, "chat", fake_chat)

    with pytest.raises(RuntimeError) as exc:
        crawler.ask_llm_decision(
            question="Who created this website?",
            pages_visited={"https://ai-evals.io": "content"},
            available_links=[],
            model="qwen3:8b",
        )

    msg = str(exc.value)
    assert "requires Ollama" in msg
    assert "11434" in msg
    assert "https://ollama.com" in msg
    assert "https://github.com/ggml-org/llama.cpp" in msg
