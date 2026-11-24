from data_visualizer import visualize_data

def test_only_requested_chart_is_rendered(tmp_path):
    p=tmp_path/'in.csv';p.write_text('amount\n1\n2\n');out=tmp_path/'charts';out.mkdir()
    (out/'amount_bar.png').write_bytes(b'keep')
    assert visualize_data(p,output_dir=out,chart_kind='line')==0
    assert (out/'amount_line.png').read_bytes().startswith(b'\x89PNG')
    assert (out/'amount_bar.png').read_bytes()==b'keep'

def test_invalid_chart_selection_fails_without_files(tmp_path):
    p=tmp_path/'in.csv';p.write_text('amount\n1\n2\n');out=tmp_path/'charts'
    assert visualize_data(p,output_dir=out,chart_kind='unknown')==1 and not out.exists()
