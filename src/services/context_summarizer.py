import re
from collections.abc import Iterable
from difflib import SequenceMatcher
from typing import Any

from src.logger import log


class ContextSummarizer:
    """Compress raw Tavily evidence into category-based summaries for report generation."""

    CATEGORY_KEYWORDS = {
        "GLOBAL CAPITAL FLOWS": ["capital flow", "capital flows", "debt inflows", "emerging market", "flows remain", "liquidity", "fii", "dii", "equity flows"],
        "FEDERAL RESERVE": ["federal reserve", "fed", "treasury yields", "policy stability", "monetary policy", "yield"],
        "INDIA": ["india", "rbi", "infrastructure spending", "rupee", "nse", "bse", "domestic liquidity"],
        "AI INFRASTRUCTURE": ["ai infrastructure", "ai capex", "data center", "power demand", "cloud", "gpu", "semiconductor", "chip"],
        "SEMICONDUCTORS": ["semiconductor", "chip", "foundry", "tsmc", "asml", "memory", "wafer"],
        "SOVEREIGN WEALTH FUNDS": ["sovereign wealth", "sovereign", "swf", "state fund", "pension fund"],
        "INFRASTRUCTURE PROJECTS": ["infrastructure projects", "infrastructure spending", "grid", "transport", "construction", "project pipeline"],
    }

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = " ".join(str(value).split()) if value is not None else ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _sentence(text: str) -> str:
        cleaned = ContextSummarizer._clean_text(text)
        sentence = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0]
        return sentence.rstrip(". ") + "." if sentence else "Data unavailable."

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", ContextSummarizer._clean_text(text).lower()).strip()

    @staticmethod
    def _is_similar(left: str, right: str, threshold: float = 0.82) -> bool:
        return SequenceMatcher(None, self := ContextSummarizer._normalize(left), ContextSummarizer._normalize(right)).ratio() >= threshold

    def _classify(self, item: dict[str, Any]) -> str:
        text = " ".join(
            [
                self._clean_text(item.get("query")),
                self._clean_text(item.get("title")),
                self._clean_text(item.get("content")),
            ]
        ).lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "GLOBAL CAPITAL FLOWS"

    def summarize(self, raw_items: Iterable[dict[str, Any]], market_context: str | None = None) -> dict[str, Any]:
        items = [item for item in raw_items if isinstance(item, dict)]
        deduped: list[dict[str, Any]] = []

        for item in items:
            candidate = self._clean_text(item.get("title")) + " " + self._clean_text(item.get("content"))
            if any(
                SequenceMatcher(None, self._normalize(candidate), self._normalize(existing_candidate)).ratio() >= 0.82
                for existing_candidate in [self._clean_text(existing.get("title")) + " " + self._clean_text(existing.get("content")) for existing in deduped]
            ):
                continue
            deduped.append(item)

        grouped: dict[str, list[str]] = {category: [] for category in self.CATEGORY_KEYWORDS}

        for item in deduped:
            category = self._classify(item)
            summary = self._sentence(item.get("content") or item.get("title") or "Data unavailable.")
            grouped.setdefault(category, []).append(summary)

        lines = []
        for category in self.CATEGORY_KEYWORDS:
            bullets = grouped.get(category, [])
            lines.append(category)
            lines.extend(f"- {bullet}" for bullet in bullets[:2]) if bullets else lines.append("- Data unavailable.")
            lines.append("")

        summary_text = "\n".join(line for line in lines if line != "").strip()
        raw_context_parts = [self._clean_text(market_context)] if market_context else []
        raw_context_parts.extend(
            self._clean_text(item.get("title")) + " " + self._clean_text(item.get("content"))
            for item in items
        )
        raw_context = "\n".join(part for part in raw_context_parts if part)

        raw_chars = len(raw_context)
        compressed_chars = len(summary_text)
        ratio = 0.0 if raw_chars == 0 else round((1.0 - (compressed_chars / raw_chars)) * 100, 1)

        log.info("Raw context: %d chars", raw_chars)
        log.info("Compressed context: %d chars", compressed_chars)
        log.info("Compression ratio: %.1f%%", ratio)

        return {
            "summary": summary_text,
            "raw_chars": raw_chars,
            "compressed_chars": compressed_chars,
            "compression_ratio": ratio,
            "categories": grouped,
            "deduped_items": deduped,
        }
