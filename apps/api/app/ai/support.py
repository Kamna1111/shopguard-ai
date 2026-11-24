"""Simple approved-FAQ lookup used before the dedicated RAG phase."""

from __future__ import annotations

import json
import re

from app.ai.providers import AIProvider
from app.core.config import PROJECT_ROOT

KB_FILE = PROJECT_ROOT / "data" / "knowledge_base" / "shop_faq.json"
NO_EVIDENCE_ANSWER = "I don’t have an approved shop note for that question yet."
STOP_WORDS = {
    "a",
    "an",
    "and",
    "can",
    "code",
    "do",
    "for",
    "how",
    "i",
    "is",
    "it",
    "of",
    "the",
    "to",
    "what",
    "you",
    "charge",
}


def answer_question(question: str, provider: AIProvider) -> tuple[str, list[str]]:
    """Find relevant approved notes and ask the configured provider to answer from them."""
    articles = json.loads(KB_FILE.read_text(encoding="utf-8"))
    words = {
        word[:-1] if word.endswith("s") and len(word) > 4 else word
        for word in re.findall(r"[a-z0-9]+", question.lower())
        if word not in STOP_WORDS
    }
    ranked: list[tuple[int, dict[str, str]]] = []
    for article in articles:
        keywords = {
            keyword[:-1] if keyword.endswith("s") and len(keyword) > 4 else keyword
            for keyword in article["keywords"]
        }
        score = len(words & keywords)
        if score:
            ranked.append((score, article))
    selected = [
        article for _, article in sorted(ranked, key=lambda item: item[0], reverse=True)[:2]
    ]
    if not selected:
        return NO_EVIDENCE_ANSWER, []
    evidence = [{"title": item["title"], "answer": item["answer"]} for item in selected]
    answer = provider.answer_support(question, evidence)
    return answer, [item["source"] for item in selected]
