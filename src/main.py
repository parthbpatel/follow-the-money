from pathlib import Path
import sys

from src.ai.report_generator import ReportGenerator
from src.data.market_data import MarketDataFetcher
from src.data.news_fetcher import NewsFetcher


def load_prompt(report_type):

    prompt_path = Path(
        f"prompts/{report_type}.txt"
    )

    return prompt_path.read_text(
        encoding="utf-8"
    )


def build_context():

    crypto = (
        MarketDataFetcher.get_crypto_prices()
    )

    news = (
        NewsFetcher.get_reuters_news()
    )

    context = f"""
    CRYPTO:
    {crypto}

    NEWS:
    {news}
    """

    return context


def run(report_type="daily"):

    prompt = load_prompt(report_type)

    context = build_context()

    report = ReportGenerator.generate(
        prompt,
        context
    )

    print(report)


if __name__ == "__main__":
    try:
        run("daily")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
