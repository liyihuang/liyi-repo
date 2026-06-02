import akshare as ak
try:
    df = ak.stock_zh_a_hist(symbol="002714", period="daily", start_date="20210101", end_date="20250101", adjust="qfq")
    print(df.head())
    print("Success! Columns:", df.columns)
except Exception as e:
    print("Error:", e)
