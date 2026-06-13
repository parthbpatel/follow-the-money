import unittest

from src.services.context_summarizer import ContextSummarizer


class ContextSummarizerTest(unittest.TestCase):
    def test_summarize_reduces_and_groups_context(self):
        raw_items = [
            {"query": "global capital flows today", "title": "IIF says debt inflows remain dominant", "content": "IIF reports debt inflows remain dominant in emerging markets and selective flows continue into higher-quality issuers.", "url": "https://example.com/1"},
            {"query": "Federal Reserve latest policy", "title": "Fed keeps policy steady", "content": "Markets expect policy stability as Treasury yields remain a key focus.", "url": "https://example.com/2"},
            {"query": "India economy latest developments", "title": "India infrastructure spending remains strong", "content": "Infrastructure spending remains strong and RBI policy remains a major flow driver.", "url": "https://example.com/3"},
            {"query": "global capital flows today", "title": "IIF says debt inflows remain dominant", "content": "IIF reports debt inflows remain dominant in emerging markets and selective flows continue into higher-quality issuers.", "url": "https://example.com/1"},
        ]

        summarizer = ContextSummarizer()
        compressed = summarizer.summarize(raw_items, "Market data placeholder")

        self.assertIn("GLOBAL CAPITAL FLOWS", compressed["summary"])
        self.assertIn("FEDERAL RESERVE", compressed["summary"])
        self.assertIn("INDIA", compressed["summary"])
        self.assertGreater(compressed["raw_chars"], compressed["compressed_chars"])
        self.assertGreaterEqual(compressed["compression_ratio"], 0)
        self.assertLessEqual(compressed["compression_ratio"], 100)


if __name__ == "__main__":
    unittest.main()
