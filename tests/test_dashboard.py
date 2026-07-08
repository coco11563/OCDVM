from report.dashboard import render_dashboard

RESULT = {"quarter": "2026Q4", "target": 150.0, "pw_price": 148.0,
          "expected_return": 0.06, "alpha": 0.8, "cei": 0.78, "regime": "neo",
          "m_neo": 10.0, "q": 1.0, "current_price": 140.0}


def test_render_dashboard(tmp_path):
    out = tmp_path / "index.html"
    pngs = {"sotp": "sotp.png", "sensitivity": "sens.png",
            "scenarios": "scn.png", "alpha_cei": "ac.png"}
    render_dashboard(RESULT, pngs, str(out))
    html = out.read_text()
    assert "2026Q4" in html and "150" in html and "sotp.png" in html
