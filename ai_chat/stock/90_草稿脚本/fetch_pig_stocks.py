import akshare as ak
import pandas as pd
import time

stocks = {
    "牧原股份": "002714",
    "温氏股份": "300498",
    "巨星农牧": "603477",
    "华统股份": "002840",
    "神农集团": "605296",
    "唐人神": "002567"
}

data = {}
for name, code in stocks.items():
    success = False
    for attempt in range(5):
        try:
            print(f"Fetching {name} ({code}) attempt {attempt+1}...")
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20210101", end_date="20251231", adjust="qfq")
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df.set_index('日期', inplace=True)
                data[name] = df
                print(f"Successfully fetched {name}, shape: {df.shape}")
                success = True
                break
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            time.sleep(2)
    if not success:
        print(f"Failed to fetch {name} after 5 attempts.")

# Analyze Wave 1 (2021-2022) and Wave 2 (2023-2024)
def analyze_wave(df, start_bottom, end_bottom, start_top, end_top):
    # Bottom window
    bottom_df = df.loc[start_bottom:end_bottom]
    if bottom_df.empty:
        return None
    # We look for the lowest close price in the bottom window
    min_idx = bottom_df['收盘'].idxmin()
    min_val = bottom_df.loc[min_idx, '收盘']
    
    # Top window
    top_df = df.loc[start_top:end_top]
    if top_df.empty:
        return None
    max_idx = top_df['收盘'].idxmax()
    max_val = top_df.loc[max_idx, '收盘']
    
    gain = (max_val - min_val) / min_val * 100
    return min_idx, min_val, max_idx, max_val, gain

print("\n=== WAVE 1 (2021-2022) ===")
print(f"{'公司':<8}\t{'最低价日期':<10}\t{'最低价':<6}\t{'最高价日期':<10}\t{'最高价':<6}\t{'涨幅':<6}")
for name, df in data.items():
    res = analyze_wave(df, "2021-08-01", "2022-05-01", "2022-05-01", "2022-11-30")
    if res:
        min_date, min_c, max_date, max_c, gain = res
        print(f"{name:<8}\t{min_date.strftime('%Y-%m-%d'):<10}\t{min_c:6.2f}\t{max_date.strftime('%Y-%m-%d'):<10}\t{max_c:6.2f}\t{gain:5.1f}%")

print("\n=== WAVE 2 (2023-2024) ===")
print(f"{'公司':<8}\t{'最低价日期':<10}\t{'最低价':<6}\t{'最高价日期':<10}\t{'最高价':<6}\t{'涨幅':<6}")
for name, df in data.items():
    res = analyze_wave(df, "2023-08-01", "2024-04-01", "2024-04-01", "2024-11-30")
    if res:
        min_date, min_c, max_date, max_c, gain = res
        print(f"{name:<8}\t{min_date.strftime('%Y-%m-%d'):<10}\t{min_c:6.2f}\t{max_date.strftime('%Y-%m-%d'):<10}\t{max_c:6.2f}\t{gain:5.1f}%")
