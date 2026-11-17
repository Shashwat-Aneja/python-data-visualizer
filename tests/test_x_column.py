import pandas as pd
from data_visualizer import visualize_data


def test_x_labels_stay_aligned_after_missing_numeric_rows_are_dropped(tmp_path, monkeypatch):
    source = tmp_path / "sales.csv"
    pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "sales": [1, None, 3]}).to_csv(source, index=False)
    observed = []
    original = pd.Series.plot
    # Capture the selected series at the downsampling boundary, before rendering.
    import data_visualizer
    original_limit = data_visualizer.limit_plot_points
    def capture(series, limit):
        observed.append(series.index.tolist())
        return original_limit(series, limit)
    monkeypatch.setattr(data_visualizer, "limit_plot_points", capture)
    assert visualize_data(source, column="sales", output_dir=tmp_path / "charts", x_column="month") == 0
    assert observed == [["Jan", "Mar"]]
    assert visualize_data(source, column="sales", x_column="missing") == 1
