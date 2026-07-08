from backtest.event_study import EventStats
from backtest.validation import validate


def test_validate_all_true():
    s = EventStats(gap_pct=0.05, drift_pct=0.10, range_low=120.0, range_high=160.0, settle_close=150.0)
    m = validate(target=148.0, bear=120.0, bull=170.0, current_price=140.0, stats=s)
    assert m.containment is True
    assert m.direction_correct is True   # target>current and settle>current
    assert abs(m.error_pct - abs(148.0 - 150.0) / 150.0) < 1e-9
    assert m.band_hit is True


def test_validate_direction_wrong():
    s = EventStats(0.0, 0.0, 100.0, 130.0, 110.0)
    m = validate(target=150.0, bear=90.0, bull=105.0, current_price=140.0, stats=s)
    assert m.direction_correct is False   # target>current but settle<current
    assert m.band_hit is False            # settle 110 not in [90, 105]
