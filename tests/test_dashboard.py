from report.dashboard import render_dashboard
from report.commentary import build_commentary, commentary_html, commentary_markdown
from tests.conftest import make_result


def test_render_dashboard(tmp_path):
    out = tmp_path / "index.html"
    pngs = {"sotp": "sotp.png", "sensitivity": "sens.png",
            "scenarios": "scn.png", "alpha_cei": "ac.png"}
    render_dashboard(make_result(), pngs, str(out), commentary="<p>hello</p>")
    html = out.read_text()
    assert "2026Q4" in html and "144" in html and "sotp.png" in html
    assert "hello" in html


def test_commentary_is_number_driven():
    sections = build_commentary(make_result(), agent_note="Watch the debt.")
    heads = [s["h"] for s in sections]
    assert "Verdict" in heads and "What to watch next quarter" in heads
    md = commentary_markdown(sections)
    html = commentary_html(sections)
    assert "$144" in md            # target rendered
    assert "α = 0.80" in md        # alpha rendered
    assert "Watch the debt." in md  # agent note appended
    assert "<h3>" in html
