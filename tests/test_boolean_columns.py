import pandas as pd
import pytest
from data_visualizer import select_numeric_series


def test_boolean_flags_are_not_selected_as_continuous_metrics():
    frame = pd.DataFrame({"active": [True, False], "sales": [10, 20]})
    assert select_numeric_series(frame)[0] == "sales"
    with pytest.raises(ValueError, match="not numeric"):
        select_numeric_series(frame, "active")
