import pandas as pd
from data_visualizer import visualize_data

def test_datetime_labels_sort_chronologically_instead_of_lexically(tmp_path,monkeypatch):
    p=tmp_path/'in.csv';p.write_text('day,amount\n01/01/2026,2\n12/31/2025,1\n');seen=[]
    monkeypatch.setattr(pd.Series,'plot',lambda self,**kwargs:seen.append(self.copy()))
    assert visualize_data(p,column='amount',x_column='day',sort_x=True,parse_x_dates=True,output_dir=tmp_path/'out')==0
    assert seen[0].tolist()==[1,2] and str(seen[0].index.tz)=='UTC'

def test_numeric_date_labels_are_not_implicitly_epoch_offsets(tmp_path):
    p=tmp_path/'in.csv';p.write_text('day,amount\n1,2\n2,3\n')
    assert visualize_data(p,x_column='day',parse_x_dates=True,output_dir=tmp_path/'out')==1
    assert not (tmp_path/'out').exists()
