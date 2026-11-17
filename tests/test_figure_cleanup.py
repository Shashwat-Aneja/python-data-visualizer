import matplotlib.pyplot as plt
import pandas as pd
from data_visualizer import visualize_data


def test_export_failure_closes_owned_figures_only(tmp_path, monkeypatch):
    csv = tmp_path / "data.csv"
    pd.DataFrame({"sales": [1, 2]}).to_csv(csv, index=False)
    existing = plt.figure()
    before = set(plt.get_fignums())
    def fail(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(plt, "savefig", fail)
    try:
        assert visualize_data(csv, output_dir=tmp_path / "out") == 1
        assert set(plt.get_fignums()) == before
    finally:
        plt.close(existing)
