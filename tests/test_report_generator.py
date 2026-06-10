import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ai.report_generator import ReportGenerator
from src.storage.file_storage import save_report


class ReportGeneratorTest(unittest.TestCase):
    @patch("src.ai.report_generator.os.getenv", side_effect=lambda key, default=None: {
        "USE_OLLAMA": "1",
        "USE_MOCK_OPENAI": "0",
        "OLLAMA_MODEL": "qwen3",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
    }.get(key, default))
    @patch("src.ai.report_generator.get_ollama_client")
    def test_generate_uses_ollama_when_enabled(self, mock_client, _mock_getenv):
        fake_client = mock_client.return_value
        fake_client.generate.return_value = {
            "response": "1. GLOBAL CAPITAL FLOW SNAPSHOT\n\n16. CORE INSIGHT"
        }
        mock_client.return_value = (fake_client, "qwen3")

        result = ReportGenerator.generate("Use Ollama", {"context": "Market context", "sources": ["CoinGecko"]})

        self.assertIn("1. GLOBAL CAPITAL FLOW SNAPSHOT", result)
        self.assertIn("16. CORE INSIGHT", result)
        fake_client.generate.assert_called_once()
        _, kwargs = fake_client.generate.call_args
        self.assertIn("=== DATA START ===", kwargs["prompt"])
        self.assertIn("REPORT FRAMEWORK:", kwargs["prompt"])

    def test_validate_report_structure_rejects_missing_framework_headers(self):
        self.assertFalse(ReportGenerator._validate_report_structure("Free-form analysis only"))

    def test_validate_report_structure_accepts_required_headers(self):
        content = "1. GLOBAL CAPITAL FLOW SNAPSHOT\n\n16. CORE INSIGHT"
        self.assertTrue(ReportGenerator._validate_report_structure(content))


class FileStorageTest(unittest.TestCase):
    def test_save_report_creates_file_under_reports_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("src.storage.file_storage.PROJECT_ROOT", Path(tmp_dir)):
                saved_path = save_report("daily", "Report body")

            saved_file = Path(saved_path)
            self.assertTrue(saved_file.exists())
            self.assertEqual(saved_file.parent.name, "daily")
            self.assertIn("reports", saved_file.parts)
            self.assertIn("daily", saved_file.parts)
            self.assertEqual(saved_file.read_text(encoding="utf-8"), "Report body")


if __name__ == "__main__":
    unittest.main()
