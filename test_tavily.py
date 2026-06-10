import os
import unittest
from unittest.mock import patch

from src.data.tavily_search import TavilySearchService


class TavilySearchServiceTest(unittest.TestCase):
    @patch.dict(os.environ, {"TAVILY_API_KEY": "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"}, clear=False)
    @patch("src.data.tavily_search.TavilyClient")
    def test_search_returns_normalized_results(self, mock_client):
        mock_client.return_value.search.return_value = {
            "results": [
                {
                    "title": "Global capital flows update",
                    "url": "https://example.com/capital-flows",
                    "content": "Capital flows remained stable.",
                    "score": 0.91,
                }
            ]
        }

        service = TavilySearchService()
        results = service.search("global capital flows today", max_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Global capital flows update")
        self.assertEqual(results[0]["url"], "https://example.com/capital-flows")
        mock_client.return_value.search.assert_called_once_with(query="global capital flows today", max_results=1)


if __name__ == "__main__":
    unittest.main()
