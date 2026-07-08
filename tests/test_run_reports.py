import os

from run import generate_outputs

RESULT = {"quarter": "2026Q4", "target": 150.0, "pw_price": 148.0,
          "expected_return": 0.06, "alpha": 0.8, "cei": 0.78, "regime": "neo",
          "m_neo": 10.0, "q": 1.0, "current_price": 140.0,
          "ev_legacy": 300000.0, "ev_oci": 120000.0,
          "scenarios": {"Bear": 120.0, "Base": 150.0, "Bull": 180.0},
          "sensitivity": [[100, 110], [120, 130]],
          "sensitivity_axes": {"growth": [0.8, 1.0], "mneo": [8.0, 10.0]}}


def test_generate_outputs(tmp_path):
    paths = generate_outputs(RESULT, str(tmp_path))
    assert os.path.exists(paths["dashboard"])
    for k in ("sotp", "sensitivity", "scenarios", "alpha_cei"):
        assert os.path.exists(paths[k])
