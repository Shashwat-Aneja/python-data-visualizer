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


def test_explicit_complex_column_is_rejected():
    frame = pd.DataFrame({"signal": [1 + 2j, 3 + 4j]})

    with pytest.raises(ValueError, match="complex"):
        select_numeric_series(frame, "signal")


def test_automatic_selection_skips_complex_columns():
    frame = pd.DataFrame(
        {
            "complex_signal": [1 + 2j, 3 + 4j],
            "sales": [10.0, 20.0],
        }
    )

    column, series = select_numeric_series(frame)

    assert column == "sales"
    assert series.tolist() == [10.0, 20.0]


def test_visualizer_returns_failure_for_missing_input(tmp_path, capsys):
    status = visualize_data(tmp_path / "missing.csv", output_dir=tmp_path / "out")

    assert status == 1
    assert "Error processing file" in capsys.readouterr().out


def test_visualizer_cli_returns_failure_for_invalid_column(tmp_path, capsys):
    from data_visualizer import main

    csv_path = tmp_path / "sales.csv"
    pd.DataFrame({"sales": [12, 20]}).to_csv(csv_path, index=False)

    assert main([str(csv_path), "--column", "unknown", "--output-dir", str(tmp_path / "charts")]) == 1
    assert "not found" in capsys.readouterr().out


def test_visualizer_cli_returns_success_after_saving_pngs(tmp_path):
    from data_visualizer import main

    csv_path = tmp_path / "sales.csv"
    pd.DataFrame({"sales": [12, 20]}).to_csv(csv_path, index=False)
    destination = tmp_path / "charts"

    assert main([str(csv_path), "--output-dir", str(destination)]) == 0
    assert (destination / "sales_bar.png").is_file()
    assert (destination / "sales_line.png").is_file()
