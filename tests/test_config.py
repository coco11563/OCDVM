from ocdvm.config import load_config


def test_config_has_required_blocks():
    cfg = load_config("config/model_config.yaml")
    for key in ("factors", "quality", "defaults", "scenarios", "sensitivity", "calibration"):
        assert key in cfg
    assert abs(sum(s["weight"] for s in cfg["factors"]["anchors"].values()) - 1.0) < 1e-6
