import os

from run import generate_outputs
from tests.conftest import make_result


def test_generate_outputs(tmp_path):
    paths = generate_outputs(make_result(), str(tmp_path))
    assert os.path.exists(paths["dashboard"])
    for k in ("sotp", "sensitivity", "scenarios", "alpha_cei",
              "factor_breakdown", "peer_multiples", "ev_reconciliation"):
        assert os.path.exists(paths[k])


def test_generate_outputs_with_evidence(tmp_path):
    ev = {"series": {"revenue": {"2025-05-31": 57399.0, "2026-05-31": 67357.0},
                     "capex": {"2025-05-31": 21215.0, "2026-05-31": 55663.0},
                     "rpo": {"2025-05-31": 137800.0, "2026-05-31": 638000.0}},
          "oci_history": {"2025-05-31": 10226.0, "2026-05-31": 18100.0},
          "agent_note": "Test note."}
    paths = generate_outputs(make_result(), str(tmp_path), evidence=ev)
    assert os.path.exists(paths["fundamental_trends"])
    # agent note should appear in the dashboard commentary
    assert "Test note." in open(paths["dashboard"]).read()
