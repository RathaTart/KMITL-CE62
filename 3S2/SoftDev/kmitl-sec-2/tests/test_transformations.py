from transformations import normalize_columns, replace_percent
from pandas import DataFrame
def test_normalize_columns():
    d = {'Col1': [1, 2, 3, 4, 7], 'Col 2': [4, 5, 6, 9, 5], 'Col3': [7, 8, 12, 1, 11]}
    df = DataFrame(data=d)
    normalize_columns(df)
    expected_cols = ['col1', 'col_2', 'col3']
    assert df.columns.tolist() == expected_cols
def test_replace_percent():
    d = {"col1": [1, 2, 3, 4],"pct": ['10%', '10', '10 %', '18. %']}
    df = DataFrame(data=d)
    df["pct"] = replace_percent(df["pct"])
    assert df["pct"].values.tolist() == [0.1, 0.1, 0.1, 0.18]