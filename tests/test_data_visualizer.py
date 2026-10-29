import numpy as np
import pandas as pd
import pytest

from data_visualizer import select_numeric_series, visualize_data


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


def test_numeric_selection_ignores_infinite_observations():
    frame = pd.DataFrame(
        {
            "infinite_only": [np.inf, -np.inf],
            "sales": [10.0, np.inf, None, 30.0],
        }
    )

    column, series = select_numeric_series(frame, "sales")
    assert column == "sales"
    assert series.tolist() == [10.0, 30.0]

    selected, automatic_series = select_numeric_series(frame)
    assert selected == "sales"
    assert automatic_series.tolist() == [10.0, 30.0]


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


def test_visualizer_saves_both_charts_without_opening_windows(tmp_path, monkeypatch, capsys):
    csv_path = tmp_path / "sales.csv"
    pd.DataFrame({"sales": [10, 20, 15]}).to_csv(csv_path, index=False)
    output_dir = tmp_path / "nested" / "charts"

    def fail_show():
        raise AssertionError("headless chart export must not open a window")

    monkeypatch.setattr("matplotlib.pyplot.show", fail_show)

    visualize_data(csv_path, column="sales", output_dir=output_dir)

    assert (output_dir / "sales_bar.png").is_file()
    assert (output_dir / "sales_line.png").is_file()
    assert (output_dir / "sales_bar.png").stat().st_size > 0
    assert (output_dir / "sales_line.png").stat().st_size > 0
    assert "Visualizing column: sales" in capsys.readouterr().out
