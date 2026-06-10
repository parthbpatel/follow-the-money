from pathlib import Path
import os
import sys

from dotenv import load_dotenv

from src.ai.report_generator import ReportGenerator
from src.logger import log
from src.services.context_builder import ContextBuilder
from src.storage.file_storage import save_report

load_dotenv()


def load_prompt(report_type):

    prompt_path = Path(f"prompts/{report_type}.txt")
    log.info("Loading prompt from %s", prompt_path)

    return prompt_path.read_text(encoding="utf-8")


def build_context():
    log.info("Building grounded market and news context")
    builder = ContextBuilder()
    return builder.build()


def run(report_type="daily"):

    log.info("Starting report generation for type=%s", report_type)
    prompt = load_prompt(report_type)

    context = build_context()
    log.info("Context size: %d characters", len(context["context"]))
    log.info("Generating report with %s backend", "Ollama" if os.getenv("USE_OLLAMA", "1").lower() in {"1", "true", "yes"} else "OpenAI")

    report = ReportGenerator.generate(prompt, context)
    log.info("Report generation finished successfully.")

    saved_path = save_report(report_type, report)
    log.info("Report saved to %s", saved_path)
    print(f"\nReport saved to: {saved_path}\n")
    print(report)


if __name__ == "__main__":
    try:
        run("daily")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
