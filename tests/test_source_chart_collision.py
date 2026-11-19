import data_visualizer as app
def test_chart_never_overwrites_csv_with_png_extension(tmp_path):
    source=tmp_path/'value_bar.png';source.write_text('value\n1\n2\n')
    assert app.visualize_data(source,output_dir=tmp_path)==1
    assert source.read_text()=='value\n1\n2\n'
def test_hardlink_alias_is_protected_before_any_output(tmp_path):
    source=tmp_path/'data.csv';source.write_text('value\n1\n2\n')
    __import__('os').link(source,tmp_path/'value_line.png')
    assert app.visualize_data(source,output_dir=tmp_path)==1
    assert not (tmp_path/'value_bar.png').exists()
