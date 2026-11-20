from data_visualizer import _reject_duplicate_headers
import pytest
def test_duplicate_headers_are_rejected_instead_of_renamed(tmp_path):
    p=tmp_path/'data.csv';p.write_text('value,value\n1,2\n')
    with pytest.raises(ValueError,match='unique'):_reject_duplicate_headers(p)
def test_bom_header_and_distinct_names_are_supported(tmp_path):
    p=tmp_path/'data.csv';p.write_text('\ufeffvalue,other\n1,2\n',encoding='utf-8')
    _reject_duplicate_headers(p)

def test_duplicate_value_columns_do_not_generate_misleading_charts(tmp_path):
    from data_visualizer import visualize_data
    p=tmp_path/'data.csv';p.write_text('value,value\n1,999\n2,999\n')
    output=tmp_path/'charts'
    assert visualize_data(p,output_dir=output)==1
    assert not output.exists()
