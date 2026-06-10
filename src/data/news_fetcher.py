from typing import Any

from src.data.tavily_search import TavilySearchService
from src.logger import log


class NewsFetcher:

    @staticmethod
    def get_macro_news() -> list[dict[str, Any]]:
        queries = [
            "global capital flows today",
            "Federal Reserve latest policy",
            "RBI latest announcement",
            "India economy latest developments",
            "AI infrastructure investments",
            "semiconductor investments",
            "sovereign wealth fund investments",
            "infrastructure spending projects",
        ]

        service = TavilySearchService()
        all_results: list[dict[str, Any]] = []

        for query in queries:
            results = service.search(query=query, max_results=3)
            for item in results:
                all_results.append({"query": query, **item})

        log.info("Fetched %d macro news items from Tavily", len(all_results))
        return all_results

    @staticmethod
    def get_reuters_news() -> list[dict[str, Any]]:
        log.warning("Reuters RSS support has been deprecated. Returning macro news from Tavily instead.")
        return NewsFetcher.get_macro_news()
