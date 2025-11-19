#!/usr/bin/env python3
"""Verify latest data in features files"""
import pandas as pd

files = {
    'Corn Features': 'data/corn_combined_features.csv',
    'Soybean Features': 'data/soybean_combined_features.csv'
}

for name, path in files.items():
    try:
        df = pd.read_csv(path, parse_dates=['date'])
        print(f"\n{name}:")
        print(f"  Total rows: {len(df)}")
        print(f"  Total cols: {len(df.columns)}")
        print(f"  Latest date: {df['date'].max()}")
        print(f"  Latest price: ${df.iloc[-1]['close']:.2f}")
        print(f"  Last 3 dates:")
        for i in range(-3, 0):
            row = df.iloc[i]
            print(f"    {row['date']}: ${row['close']:.2f}")
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")
