import json

from data.fetch_oracle import parse_us_gaap_concept, latest_ttm


def test_parse_and_ttm():
    with open("tests/fixtures/orcl_companyconcept_sample.json") as f:
        js = json.load(f)
    vals = parse_us_gaap_concept(js)
    assert len(vals) >= 4
    assert vals[0]["end"] <= vals[-1]["end"]  # sorted ascending
    ttm = latest_ttm(vals)
    # last 4 quarterly (10-Q) points summed, in $M
    assert ttm > 0
    assert ttm == (14130 + 14930 + 16200 + 16800)  # skips the 10-K row
