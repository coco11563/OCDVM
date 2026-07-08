from ocdvm.sensitivity import sensitivity_grid
from tests.conftest import make_inputs


def test_grid_shape_and_monotonic_in_multiple():
    g = sensitivity_grid(make_inputs(), 0.8, 1.0, growth_axis=[1.0, 1.2], mneo_axis=[8.0, 12.0])
    assert g.shape == (2, 2)
    assert g[0, 1] > g[0, 0]
    assert g[1, 0] > g[0, 0]
