import pandas as pd
import pytest
from data_visualizer import select_numeric_series


@pytest.mark.parametrize("column", [None, "sales"])
def test_duplicate_column_labels_have_clear_validation_error(column):
    frame = pd.DataFrame([[1, 2]], columns=["sales", "sales"])
    with pytest.raises(ValueError, match="unique"):
        select_numeric_series(frame, column)
