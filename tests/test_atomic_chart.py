from pathlib import Path
import pytest
import data_visualizer


def test_partial_render_cannot_truncate_previous_chart(tmp_path, monkeypatch):
    output = tmp_path / "chart.png"
    output.write_bytes(b"previous png")
    def fail(path, **kwargs):
        Path(path).write_bytes(b"partial")
        raise OSError("disk full")
    monkeypatch.setattr(data_visualizer.plt, "savefig", fail)
    with pytest.raises(OSError, match="disk full"):
        data_visualizer.save_chart_atomic(output)
    assert output.read_bytes() == b"previous png"
    assert list(tmp_path.iterdir()) == [output]
