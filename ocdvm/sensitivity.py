import numpy as np
from dataclasses import replace

from ocdvm.units import QuarterInputs
from ocdvm.valuation import value_company


def sensitivity_grid(inp: QuarterInputs, base_alpha: float, q: float,
                     growth_axis, mneo_axis) -> np.ndarray:
    grid = np.zeros((len(growth_axis), len(mneo_axis)))
    for i, gmult in enumerate(growth_axis):
        inp2 = replace(inp, rev_oci_ttm=inp.rev_oci_ttm * gmult)
        for j, mneo in enumerate(mneo_axis):
            grid[i, j] = value_company(inp2, base_alpha, mneo, q).target
    return grid
