import os

from report.plots import plot_sotp, plot_sensitivity

RESULT = {"ev_legacy": 300000.0, "ev_oci": 120000.0, "target": 150.0,
          "sensitivity": [[100, 110], [120, 130]],
          "sensitivity_axes": {"growth": [0.8, 1.0], "mneo": [8.0, 10.0]}}


def test_plots_write_png(tmp_path):
    p1 = plot_sotp(RESULT, str(tmp_path / "sotp.png"))
    p2 = plot_sensitivity(RESULT, str(tmp_path / "sens.png"))
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0
