from datetime import datetime
from pathlib import Path

from src.logger import log

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def save_report(report_type: str, content: str) -> str:
    """Save a generated report to the reports/<type>/ folder."""
    safe_type = (report_type or "daily").strip().lower()
    report_dir = PROJECT_ROOT / "reports" / safe_type
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = report_dir / f"{safe_type}-{timestamp}.txt"
    file_path.write_text(content, encoding="utf-8")

    log.info("Saved report to %s", file_path)
    return str(file_path)
