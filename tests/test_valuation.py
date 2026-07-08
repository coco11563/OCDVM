import pytest

from ocdvm.valuation import ev_legacy, ev_oci, value_company
from tests.conftest import make_inputs


def test_ev_legacy():
    assert ev_legacy(23800.0, 13.0) == 23800.0 * 13.0


def test_ev_oci_migration_blend():
    assert ev_oci(1.0, 12000.0, 10.0, 1.0, 1200.0, 20.0) == 12000.0 * 10.0
    assert ev_oci(0.0, 12000.0, 10.0, 1.0, 1200.0, 20.0) == 1200.0 * 20.0
    assert ev_oci(0.8, 12000.0, 10.0, 1.1, 1200.0, 20.0) == pytest.approx(
        0.8 * 12000.0 * 10.0 * 1.1 + 0.2 * 1200.0 * 20.0)


def test_value_company_target_price():
    inp = make_inputs()
    r = value_company(inp, alpha=0.8, m_neo=10.0, q=1.0)
    legacy = (25000.0 - 1200.0) * 13.0
    oci = 0.8 * 12000.0 * 10.0 * 1.0 + 0.2 * 1200.0 * 20.0
    ev = legacy + oci
    assert r.ev_total == ev
    assert r.equity == ev - 76000.0
    assert r.target == (ev - 76000.0) / 2800.0
