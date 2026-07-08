import yaml
from dataclasses import fields

from ocdvm.units import QuarterInputs

_OPTIONAL = {"customer_concentration"}


def load_inputs(path: str) -> QuarterInputs:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    raw.pop("meta", None)
    names = {f.name for f in fields(QuarterInputs)}
    missing = [n for n in names if n not in raw and n not in _OPTIONAL]
    if missing:
        raise ValueError(f"inputs missing required fields: {sorted(missing)}")
    kwargs = {n: raw.get(n) for n in names}
    return QuarterInputs(**kwargs)
