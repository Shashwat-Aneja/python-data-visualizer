import pandas as pd
import pytest
from data_visualizer import limit_plot_points


def test_sampling_bounds_plot_size_and_preserves_endpoints():
    values = pd.Series(range(10000))
    result = limit_plot_points(values, 100)
    assert len(result) == 100
    assert result.iloc[0] == 0 and result.iloc[-1] == 9999
    assert result.index.is_monotonic_increasing


@pytest.mark.parametrize("limit", [0, 1, True, 2.5])
def test_invalid_plot_limits_are_rejected(limit):
    with pytest.raises(ValueError, match="max_points"):
        limit_plot_points(pd.Series([1, 2]), limit)
