from io import StringIO
import os
import pandas as pd
from data_visualizer import visualize_data

def test_memory_stream_data_and_chart_exports(tmp_path,monkeypatch):
    monkeypatch.setattr(pd.Series,'plot',lambda *a,**kw:None)
    source=StringIO('value\n1\n2\n3\n')
    out=tmp_path/'data.csv';summary=tmp_path/'s.json'
    assert visualize_data(source,data_output=out,output_dir=tmp_path/'charts',summary_output=summary,chart_kind='line')==0
    assert pd.read_csv(out).value.tolist()==[1,2,3] and not source.closed

def test_open_file_and_hardlink_aliases_are_protected(tmp_path):
    source=tmp_path/'a.csv';source.write_text('value\n1\n2\n')
    alias=tmp_path/'alias.csv';os.link(source,alias)
    with source.open() as stream:
        assert visualize_data(stream,data_output=alias,output_dir=tmp_path/'charts')==1
    assert source.read_text()=='value\n1\n2\n'
