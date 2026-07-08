from ocdvm.units import ebitda_oci, legacy_ebitda
from tests.conftest import make_inputs


def test_ebitda_oci_from_margin():
    inp = make_inputs(rev_oci_ttm=12000.0, oci_op_margin=0.10)
    assert ebitda_oci(inp) == 1200.0


def test_legacy_ebitda_is_total_minus_oci():
    inp = make_inputs(total_ebitda=25000.0, rev_oci_ttm=12000.0, oci_op_margin=0.10)
    assert legacy_ebitda(inp) == 25000.0 - 1200.0
