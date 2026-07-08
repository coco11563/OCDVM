from dataclasses import dataclass

from backtest.event_study import EventStats


@dataclass
class ValidationMetrics:
    containment: bool
    direction_correct: bool
    error_pct: float
    band_hit: bool


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def validate(target: float, bear: float, bull: float,
             current_price: float, stats: EventStats) -> ValidationMetrics:
    settle = stats.settle_close
    containment = stats.range_low <= target <= stats.range_high
    direction_correct = _sign(target - current_price) == _sign(settle - current_price)
    error_pct = abs(target - settle) / settle if settle else float("inf")
    lo, hi = min(bear, bull), max(bear, bull)
    band_hit = lo <= settle <= hi
    return ValidationMetrics(containment, direction_correct, error_pct, band_hit)
