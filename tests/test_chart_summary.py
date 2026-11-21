import json
from data_visualizer import visualize_data
def test_summary_distinguishes_filtered_and_sampled_rows(tmp_path):
    source=tmp_path/'data.csv';source.write_text('value\n1\nNaN\ninf\n2\n3\n')
    summary=tmp_path/'summary.json'
    assert visualize_data(source,output_dir=tmp_path/'charts',max_points=2,summary_output=summary,histogram=True)==0
    assert json.loads(summary.read_text())=={'column':'value','input_rows':5,'usable_rows':3,'dropped_rows':2,'plotted_rows':2,'histogram_rows':3}
def test_summary_cannot_alias_source_or_chart(tmp_path):
    source=tmp_path/'data.csv';source.write_text('value\n1\n2\n')
    assert visualize_data(source,output_dir=tmp_path,summary_output=source)==1
    assert source.read_text()=='value\n1\n2\n'
    assert visualize_data(source,output_dir=tmp_path,summary_output=tmp_path/'value_bar.png')==1
    assert not (tmp_path/'value_bar.png').exists()
