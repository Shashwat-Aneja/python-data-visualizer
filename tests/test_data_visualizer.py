import pandas as pd
import pytest

from data_visualizer import select_numeric_series


def test_explicit_numeric_column_is_selected_and_missing_rows_are_dropped():
    frame = pd.DataFrame({"sales": [10, None, 30], "cost": [2, 3, 4]})

    column, series = select_numeric_series(frame, "sales")

    assert column == "sales"
    assert series.tolist() == [10, 30]


def test_automatic_selection_skips_numeric_columns_without_values():
    frame = pd.DataFrame(
        {
            "empty_metric": pd.Series([None, None], dtype="float64"),
            "active_metric": [4, 9],
        }
    )

    column, series = select_numeric_series(frame)

    assert column == "active_metric"
    assert series.tolist() == [4, 9]


def test_explicit_selection_rejects_unknown_or_non_numeric_columns():
    frame = pd.DataFrame({"label": ["a", "b"], "value": [1, 2]})

    with pytest.raises(ValueError, match="not found"):
        select_numeric_series(frame, "missing")
    with pytest.raises(ValueError, match="not numeric"):
        select_numeric_series(frame, "label")


def test_selection_rejects_empty_numeric_data():
    frame = pd.DataFrame({"value": pd.Series([None, None], dtype="float64")})

    with pytest.raises(ValueError, match="no usable values"):
        select_numeric_series(frame, "value")
