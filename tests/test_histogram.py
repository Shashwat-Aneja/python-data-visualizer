import data_visualizer as app
def test_histogram_uses_full_data_and_creates_output(tmp_path,monkeypatch):
    source=tmp_path/'data.csv';source.write_text('value\n1\n2\n3\n4\n5\n')
    seen=[];hist=app.plt.hist
    def capture(values,**options):
        seen.extend(values);return hist(values,**options)
    monkeypatch.setattr(app.plt,'hist',capture)
    assert app.visualize_data(source,output_dir=tmp_path/'out',max_points=2,histogram=True)==0
    assert seen==[1,2,3,4,5]
    assert (tmp_path/'out'/'value_histogram.png').stat().st_size>0
