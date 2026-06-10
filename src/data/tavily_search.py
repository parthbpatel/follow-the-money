import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

from src.logger import log

load_dotenv()


class TavilySearchService:
    """Thin wrapper around the Tavily client for evidence-based research."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY is not set. Add it to your environment before running searches.")

        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute a Tavily search and normalize the returned results."""
        log.info("Tavily search started for query=%s", query)

        try:
            response = self.client.search(query=query, max_results=max_results)
        except Exception as exc:
            log.exception("Tavily search failed for query=%s", query)
            raise RuntimeError("Tavily search failed. Check the API key and network connection.") from exc

        results = response.get("results", []) if isinstance(response, dict) else []
        normalized = []

        for item in results:
            normalized.append(
                {
                    "title": item.get("title") or "Untitled result",
                    "url": item.get("url") or "",
                    "content": item.get("content") or item.get("snippet") or "",
                    "score": item.get("score"),
                }
            )

        log.info("Tavily search completed for query=%s with %d result(s)", query, len(normalized))
        return normalized
