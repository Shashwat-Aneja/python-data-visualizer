import pandas as pd
import data_visualizer


def test_numeric_x_column_is_not_reused_as_automatic_y(tmp_path, monkeypatch):
    source = tmp_path / "data.csv"
    pd.DataFrame({"month": [1, 2, 3], "sales": [20, 30, 40]}).to_csv(source, index=False)
    observed = []
    original = data_visualizer.limit_plot_points
    def capture(series, limit):
        observed.append((series.name, series.tolist()))
        return original(series, limit)
    monkeypatch.setattr(data_visualizer, "limit_plot_points", capture)
    assert data_visualizer.visualize_data(source, x_column="month", output_dir=tmp_path / "charts") == 0
    assert observed == [("sales", [20, 30, 40])]
