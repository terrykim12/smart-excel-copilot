import os, json
from app.io.loader import load_table
from app.core.profile import profile_dataframe
from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe

SRC = 'data/samples/transactions_utf8.csv'

def run():
    df = load_table(SRC)
    prof = profile_dataframe(df, sample_rows=10000)
    print('[profile] columns:', [c['name'] for c in prof['columns']])
    df2 = level1_clean(df, currency_split=True, date_fmt='YYYY-MM-DD', drop_empty_rows=True, drop_empty_cols=True)
    df3 = dedupe(df2, keys=['거래id'], keep_policy='last_by:업데이트일')
    print('[demo] before/after rows:', len(df), len(df3))

if __name__ == '__main__':
    run()
