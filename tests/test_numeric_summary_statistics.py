import json,pytest
from data_visualizer import visualize_data,numeric_statistics

def test_summary_statistics_cover_unsampled_finite_observations(tmp_path):
    p=tmp_path/'in.csv';p.write_text('amount\n1\n100\n3\n');out=tmp_path/'summary.json'
    assert visualize_data(p,output_dir=tmp_path/'charts',max_points=2,summary_output=out,summary_stats=True)==0
    data=json.loads(out.read_text())
    assert data['plotted_rows']==2 and data['statistics']['maximum']==100
    assert data['statistics']['median']==3 and data['statistics']['mean']==pytest.approx(104/3)

def test_large_finite_mean_and_even_median_do_not_overflow():
    result=numeric_statistics([1e308,1e308])
    assert result['mean']==result['median']==1e308

def test_mean_and_even_median_preserve_large_cancellation_residuals():
    result=numeric_statistics([1e16,-9999999999999998.0])
    assert result['mean']==result['median']==1.0
    assert numeric_statistics([1e308,1e-20,-1e308])['mean']==1e-20/3

def test_mean_preserves_cancellation_when_an_intermediate_sum_overflows():
    assert numeric_statistics([1e308,1e308,-1e308,-1e308])['mean']==0
