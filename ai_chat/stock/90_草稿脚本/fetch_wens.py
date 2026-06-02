import akshare as ak
import pandas as pd
import time

success = False
for attempt in range(10):
    try:
        print(f"Fetching 温氏股份 (300498) attempt {attempt+1}...")
        df = ak.stock_zh_a_hist(symbol="300498", period="daily", start_date="20210101", end_date="20251231", adjust="qfq")
        if not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            print("Successfully fetched Wens!")
            
            # Analyze Wave 1
            bottom1 = df.loc["2021-08-01":"2022-05-01"]
            if not bottom1.empty:
                min_idx1 = bottom1['收盘'].idxmin()
                min_val1 = bottom1.loc[min_idx1, '收盘']
                top1 = df.loc["2022-05-01":"2022-11-30"]
                max_idx1 = top1['收盘'].idxmax()
                max_val1 = top1.loc[max_idx1, '收盘']
                gain1 = (max_val1 - min_val1) / min_val1 * 100
                print(f"WAVE 1: Bottom {min_idx1.strftime('%Y-%m-%d')} ({min_val1:.2f}), Top {max_idx1.strftime('%Y-%m-%d')} ({max_val1:.2f}), Gain {gain1:.1f}%")
            
            # Analyze Wave 2
            bottom2 = df.loc["2023-08-01":"2024-04-01"]
            if not bottom2.empty:
                min_idx2 = bottom2['收盘'].idxmin()
                min_val2 = bottom2.loc[min_idx2, '收盘']
                top2 = df.loc["2024-04-01":"2024-11-30"]
                max_idx2 = top2['收盘'].idxmax()
                max_val2 = top2.loc[max_idx2, '收盘']
                gain2 = (max_val2 - min_val2) / min_val2 * 100
                print(f"WAVE 2: Bottom {min_idx2.strftime('%Y-%m-%d')} ({min_val2:.2f}), Top {max_idx2.strftime('%Y-%m-%d')} ({max_val2:.2f}), Gain {gain2:.1f}%")
                
            success = True
            break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
if not success:
    print("Failed to fetch Wens")
