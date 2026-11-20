import data_visualizer as app
def test_tiny_iqr_outlier_cannot_allocate_unbounded_histogram_bins(tmp_path,monkeypatch):
    p=tmp_path/'data.csv';p.write_text('value\n'+''.join(str(x*1e-12)+'\n' for x in range(100))+'1e100\n')
    counts=[]
    monkeypatch.setattr(app.plt,'hist',lambda values,bins:counts.append((len(values),bins)))
    assert app.visualize_data(p,output_dir=tmp_path/'out',histogram=True)==0
    assert counts[0][0]==101 and 1<=counts[0][1]<=100
