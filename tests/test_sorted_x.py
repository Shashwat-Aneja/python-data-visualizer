import pandas as pd
import data_visualizer as app
def test_x_sort_is_stable_and_happens_before_sampling(tmp_path,monkeypatch):
    p=tmp_path/'data.csv';pd.DataFrame({'day':[2,1,1],'value':[20,10,11]}).to_csv(p,index=False)
    seen=[];original=app.limit_plot_points
    def capture(series,limit):seen.extend(list(zip(series.index,series)));return original(series,limit)
    monkeypatch.setattr(app,'limit_plot_points',capture)
    assert app.visualize_data(p,column='value',x_column='day',sort_x=True,output_dir=tmp_path/'plots')==0
    assert seen==[(1,10),(1,11),(2,20)]
def test_x_sort_requires_explicit_axis(tmp_path):
    p=tmp_path/'data.csv';p.write_text('value\n1\n2\n')
    assert app.visualize_data(p,sort_x=True,output_dir=tmp_path/'plots')==1
    assert not (tmp_path/'plots').exists()
