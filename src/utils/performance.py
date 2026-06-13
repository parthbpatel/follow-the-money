import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable

from src.logger import log


class PerformanceTimer:
    """Context manager for labeled duration measurement and logging."""

    def __init__(self, label: str, *, record_key: str | None = None, enabled: bool = True) -> None:
        self.label = label
        self.record_key = record_key or label
        self.enabled = enabled
        self.start_time = 0.0
        self.duration = 0.0

    def __enter__(self) -> "PerformanceTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.duration = time.perf_counter() - self.start_time
        PerformanceMetrics.record(self.record_key, self.duration)
        if self.enabled:
            log.info("[PERF] %s took %.2f sec", self.label, self.duration)


class PerformanceMetrics:
    """Simple cumulative tracker for profiling summaries."""

    _timings: dict[str, float] = defaultdict(float)

    @classmethod
    def record(cls, key: str, duration: float) -> None:
        cls._timings[key] += duration

    @classmethod
    def get(cls, key: str) -> float:
        return float(cls._timings.get(key, 0.0))

    @classmethod
    def reset(cls) -> None:
        cls._timings.clear()

    @classmethod
    def summary(cls) -> dict[str, float]:
        return dict(cls._timings)


def timing(label: str | None = None) -> Callable:
    """Decorator that measures function duration and logs it."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timer_label = label or func.__name__.replace("_", " ").title()
            with PerformanceTimer(timer_label):
                return func(*args, **kwargs)

        return wrapper

    return decorator
