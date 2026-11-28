import pandas as pd
from data_visualizer import visualize_data

def test_export_matches_sampled_endpoints(tmp_path,monkeypatch):
    src=tmp_path/'a.csv';out=tmp_path/'data.csv'
    src.write_text('value\n1\n2\n3\n4\n')
    monkeypatch.setattr(pd.Series,'plot',lambda *a,**kw:None)
    assert visualize_data(src,max_points=2,data_output=out,output_dir=tmp_path/'charts',chart_kind='line')==0
    assert pd.read_csv(out).value.tolist()==[1,4]

def test_export_alias_fails_before_chart_write(tmp_path):
    src=tmp_path/'a.csv';src.write_text('value\n1\n2\n')
    assert visualize_data(src,data_output=src,output_dir=tmp_path/'charts')==1
    assert not list((tmp_path/'charts').glob('*.png'))
    assert src.read_text()=='value\n1\n2\n'
