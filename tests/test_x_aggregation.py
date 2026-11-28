import json
import pandas as pd
from data_visualizer import visualize_data

def test_grouped_series_preserves_raw_distribution(tmp_path,monkeypatch):
    src=tmp_path/"a.csv";summary=tmp_path/"s.json"
    src.write_text("label,value\nA,1\nA,3\nB,10\n")
    plotted=[]
    monkeypatch.setattr(pd.Series,'plot',lambda self,*a,**kw:plotted.append(self.tolist()))
    assert visualize_data(src,column='value',x_column='label',aggregate_x='mean',output_dir=tmp_path/'charts',summary_output=summary,summary_stats=True,chart_kind='line')==0
    data=json.loads(summary.read_text())
    assert plotted==[[2,10]] and data['usable_rows']==3 and data['aggregated_points']==2
    assert data['statistics']['mean']==14/3
