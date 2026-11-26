import json
from data_visualizer import main

def test_histogram_only_renders_full_distribution_without_sampled_charts(tmp_path):
    source=tmp_path/'in.csv';source.write_text('amount\n1\n100\n3\n');charts=tmp_path/'out';summary=tmp_path/'summary.json'
    assert main([str(source),'--chart-kind','histogram','--output-dir',str(charts),'--summary-output',str(summary),'--max-points','2'])==0
    assert sorted(p.name for p in charts.iterdir())==['amount_histogram.png']
    data=json.loads(summary.read_text())
    assert data['plotted_rows']==0 and data['histogram_rows']==data['usable_rows']==3
