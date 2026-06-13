from datetime import datetime
from pathlib import Path
import os
import sys
import time

from dotenv import load_dotenv

from src.ai.report_generator import ReportGenerator
from src.logger import log
from src.services.context_builder import ContextBuilder
from src.services.context_summarizer import ContextSummarizer
from src.storage.file_storage import save_report
from src.utils.performance import PerformanceMetrics, PerformanceTimer

load_dotenv()


def load_prompt(report_type):

    prompt_path = Path("prompts") / f"{report_type}.txt"
    log.info("Loading prompt from %s", prompt_path)

    with PerformanceTimer("Prompt Loading", record_key="Prompt Loading"):
        prompt = prompt_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        return prompt.replace("[INSERT TODAYS DATE]", today)


def build_context():
    log.info("Building grounded market and news context")
    with PerformanceTimer("Context Builder", record_key="Context Builder"):
        builder = ContextBuilder()
        return builder.build()


def compress_context(raw_context: dict) -> dict:
    with PerformanceTimer("Compression", record_key="Compression"):
        summarizer = ContextSummarizer()
        compressed = summarizer.summarize(raw_context.get("news_items", []), raw_context.get("context", ""))

    return {
        **raw_context,
        "context": compressed["summary"],
        "compressed_context": compressed["summary"],
        "raw_context": raw_context.get("context", ""),
        "compression_stats": {
            "raw_chars": compressed["raw_chars"],
            "compressed_chars": compressed["compressed_chars"],
            "compression_ratio": compressed["compression_ratio"],
        },
    }


def run(report_type="daily"):

    PerformanceMetrics.reset()
    started_at = time.time()
    log.info("Starting report generation for type=%s", report_type)
    prompt = load_prompt(report_type)

    context = build_context()
    compressed_context = compress_context(context)
    log.info("Raw context size: %d characters", compressed_context["compression_stats"]["raw_chars"])
    log.info("Compressed context size: %d characters", compressed_context["compression_stats"]["compressed_chars"])
    log.info("Compression ratio: %.1f%%", compressed_context["compression_stats"]["compression_ratio"])
    log.info("Generating report with %s backend", "Ollama" if os.getenv("USE_OLLAMA", "1").lower() in {"1", "true", "yes"} else "OpenAI")

    report = ReportGenerator.generate(prompt, compressed_context)
    log.info("Report generation finished successfully.")

    with PerformanceTimer("File Save", record_key="File Save"):
        saved_path = save_report(report_type, report)
    elapsed_seconds = time.time() - started_at
    log.info("Report saved to %s in %.2f seconds", saved_path, elapsed_seconds)
    print(f"\nReport saved to: {saved_path}\n")
    print(report)

    metrics = PerformanceMetrics.summary()
    print("\n================================================")
    print("PERFORMANCE SUMMARY")
    print(f"Prompt Loading: {metrics.get('Prompt Loading', 0):.2f} sec")
    print(f"CoinGecko: {metrics.get('CoinGecko', 0):.2f} sec")
    print(f"Tavily Total: {metrics.get('Tavily Total', 0):.2f} sec")
    print(f"Context Builder: {metrics.get('Context Builder', 0):.2f} sec")
    print(f"Compression: {metrics.get('Compression', 0):.2f} sec")
    print(f"Prompt Construction: {metrics.get('Prompt Construction', 0):.2f} sec")
    print(f"Ollama Generation: {metrics.get('Ollama Generation', 0):.2f} sec")
    print(f"Validation: {metrics.get('Validation', 0):.2f} sec")
    print(f"Retry Generation: {metrics.get('Retry Generation', 0):.2f} sec")
    print(f"File Save: {metrics.get('File Save', 0):.2f} sec")
    print(f"TOTAL: {elapsed_seconds:.2f} sec")
    print("================================================")


if __name__ == "__main__":
    try:
        run("daily")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
