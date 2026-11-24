from data_visualizer import visualize_data

def test_log_scale_rejects_nonpositive_data_before_export(tmp_path):
    p=tmp_path/'in.csv';p.write_text('amount\n0\n10\n');out=tmp_path/'charts'
    assert visualize_data(p,output_dir=out,log_y=True)==1
    assert not out.exists()

def test_positive_values_render_logarithmic_charts(tmp_path):
    p=tmp_path/'in.csv';p.write_text('amount\n1\n1000\n');out=tmp_path/'charts'
    assert visualize_data(p,output_dir=out,log_y=True)==0
    assert sorted(f.name for f in out.iterdir())==['amount_bar.png','amount_line.png']
