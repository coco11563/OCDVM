from ocdvm.peers import Peer
from ocdvm.config import load_config
from run import assemble_result, append_history
from tests.conftest import make_inputs


def test_assemble_result_keys():
    cfg = load_config("config/model_config.yaml")
    peers = [Peer("CRWV", 5000.0, 100.0, 480.0, 8000.0),
             Peer("NBIS", 1200.0, 40.0, 230.0, 0.0)]
    r = assemble_result(make_inputs(), cfg, peers, cfg["quality"]["subscores"])
    for k in ("alpha", "m_neo", "q", "target", "ev_legacy", "ev_oci",
              "scenarios", "pw_price", "expected_return", "sensitivity", "cei", "regime"):
        assert k in r
    assert 0.0 <= r["alpha"] <= 1.0


def test_append_history(tmp_path):
    p = tmp_path / "h.csv"
    append_history(str(p), {"quarter": "2026Q4", "alpha": 0.8, "target": 150.0})
    append_history(str(p), {"quarter": "2027Q1", "alpha": 0.7, "target": 160.0})
    assert p.read_text().count("\n") == 3   # header + 2 rows
