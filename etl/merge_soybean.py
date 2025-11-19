#!/usr/bin/env python3
import pandas as pd
from dateutil.relativedelta import relativedelta

PRICES = "data/soybean_prices.csv"
COT = "data/cot_soybean.csv"
CFTC_OPTIONS = "data/cftc_options_soybean.csv"
WASDE = "data/wasde_soybean.csv"
CROP_CONDITIONS = "data/crop_conditions_soybean.csv"
WEATHER_INDEX = "data/weather_soybean_belt_index.csv"
CURRENCY = "data/currency_data.csv"  # Shared with corn
OUT = "data/soybean_combined.csv"

def main():
    print("="*80)
    print("MERGING SOYBEAN DATA FILES")
    print("="*80)

    # Load price data
    try:
        prices = pd.read_csv(PRICES, parse_dates=["date"])
        print(f"✓ Loaded prices: {len(prices):,} rows")
    except FileNotFoundError:
        print(f"✗ ERROR: {PRICES} not found. Please run: python etl/soybean_prices_yahoo.py")
        return

    # Load and process COT data (weekly -> daily via forward-fill)
    try:
        cot = pd.read_csv(COT, parse_dates=["date"])
        # Remove rows with NaT dates, duplicate dates, then sort
        cot = cot.dropna(subset=["date"])
        cot = cot.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        # Forward-fill weekly COT to daily for merging on calendar days
        cot_indexed = cot.set_index("date")
        cot_daily = cot_indexed.reindex(pd.date_range(cot_indexed.index.min(), cot_indexed.index.max(), freq="D"))
        cot_daily = cot_daily.ffill().reset_index().rename(columns={"index": "date"})
        print(f"✓ Loaded COT data: {len(cot):,} rows (weekly) -> {len(cot_daily):,} rows (daily)")
    except FileNotFoundError:
        print(f"⚠ Warning: {COT} not found. Skipping COT data.")
        cot_daily = pd.DataFrame()

    # WASDE monthly; we forward-fill daily as well
    try:
        wasde = pd.read_csv(WASDE, parse_dates=["date"])
        wasde = wasde.dropna(subset=["date"])
        wasde = wasde.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        if len(wasde) > 0:
            wasde_indexed = wasde.set_index("date")
            wasde_daily = wasde_indexed.reindex(pd.date_range(wasde_indexed.index.min(), wasde_indexed.index.max(), freq="D"))
            wasde_daily = wasde_daily.ffill().reset_index().rename(columns={"index": "date"})
            print(f"✓ Loaded WASDE data: {len(wasde):,} rows (monthly) -> {len(wasde_daily):,} rows (daily)")
        else:
            wasde_daily = wasde  # Empty dataframe
            print(f"⚠ Warning: WASDE data is empty")
    except FileNotFoundError:
        print(f"⚠ Warning: {WASDE} not found. Skipping WASDE data.")
        wasde_daily = pd.DataFrame()

    # Crop conditions weekly; forward-fill to daily
    try:
        crop_conditions = pd.read_csv(CROP_CONDITIONS, parse_dates=["date"])
        crop_conditions = crop_conditions.dropna(subset=["date"])
        crop_conditions = crop_conditions.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        if len(crop_conditions) > 0:
            crop_indexed = crop_conditions.set_index("date")
            crop_daily = crop_indexed.reindex(pd.date_range(crop_indexed.index.min(), crop_indexed.index.max(), freq="D"))
            crop_daily = crop_daily.ffill().reset_index().rename(columns={"index": "date"})
            print(f"✓ Loaded crop conditions: {len(crop_conditions):,} rows (weekly) -> {len(crop_daily):,} rows (daily)")
        else:
            crop_daily = crop_conditions  # Empty dataframe
            print(f"⚠ Warning: Crop conditions data is empty")
    except FileNotFoundError:
        print(f"⚠ Warning: {CROP_CONDITIONS} not found. Skipping crop conditions data.")
        crop_daily = pd.DataFrame()

    # CFTC Options data (futures+options combined); weekly, forward-fill to daily
    try:
        cftc_options = pd.read_csv(CFTC_OPTIONS, parse_dates=["date"])
        cftc_options = cftc_options.dropna(subset=["date"])
        cftc_options = cftc_options.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        if len(cftc_options) > 0:
            options_indexed = cftc_options.set_index("date")
            options_daily = options_indexed.reindex(pd.date_range(options_indexed.index.min(), options_indexed.index.max(), freq="D"))
            options_daily = options_daily.ffill().reset_index().rename(columns={"index": "date"})
            print(f"✓ Loaded CFTC options: {len(cftc_options):,} rows (weekly) -> {len(options_daily):,} rows (daily)")
        else:
            options_daily = cftc_options
            print(f"⚠ Warning: CFTC options data is empty")
    except FileNotFoundError:
        print(f"⚠ Warning: {CFTC_OPTIONS} not found. Skipping CFTC options data.")
        options_daily = pd.DataFrame()

    # Weather index (daily); already in daily format
    try:
        weather = pd.read_csv(WEATHER_INDEX, parse_dates=["date"])
        weather = weather.dropna(subset=["date"])
        weather = weather.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        print(f"✓ Loaded weather data: {len(weather):,} rows (daily)")
    except FileNotFoundError:
        print(f"⚠ Warning: {WEATHER_INDEX} not found. Skipping weather data.")
        weather = pd.DataFrame()

    # Currency data - OPTIONAL (shared with corn, kept in currency_data.csv for future analysis)
    # To enable: uncomment the lines below
    # try:
    #     currency = pd.read_csv(CURRENCY, parse_dates=["date"])
    #     currency = currency.dropna(subset=["date"])
    #     currency = currency.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    #     print(f"✓ Loaded currency data: {len(currency):,} rows")
    # except FileNotFoundError:
    #     print(f"⚠ Warning: {CURRENCY} not found. Skipping currency data.")
    #     currency = pd.DataFrame()

    print("\n" + "="*80)
    print("MERGING DATASETS")
    print("="*80)

    # Merge all datasets (left join on prices to preserve all price dates)
    df = prices.copy()
    print(f"Starting with prices: {len(df):,} rows")

    if len(cot_daily) > 0:
        df = df.merge(cot_daily, on="date", how="left")
        print(f"  + COT data: {len(df):,} rows")

    if len(wasde_daily) > 0:
        df = df.merge(wasde_daily, on="date", how="left")
        print(f"  + WASDE data: {len(df):,} rows")

    if len(crop_daily) > 0:
        df = df.merge(crop_daily, on="date", how="left")
        print(f"  + Crop conditions: {len(df):,} rows")

    if len(options_daily) > 0:
        df = df.merge(options_daily, on="date", how="left")
        print(f"  + CFTC options: {len(df):,} rows")

    if len(weather) > 0:
        df = df.merge(weather, on="date", how="left")
        print(f"  + Weather data: {len(df):,} rows")

    # Currency merge disabled by default - uncomment above and below to re-enable
    # if len(currency) > 0:
    #     df = df.merge(currency, on="date", how="left")
    #     # Forward-fill currency data for any missing dates (though should be minimal)
    #     currency_cols = [col for col in df.columns if col.startswith(('dxy_', 'usd_', 'competitiveness_'))]
    #     df[currency_cols] = df[currency_cols].ffill()
    #     print(f"  + Currency data: {len(currency_cols)} currency columns added")

    print("\n" + "="*80)
    print("CALCULATING DERIVED METRICS")
    print("="*80)

    # Derived metrics
    df["ret_1d"] = df["close"].pct_change()
    df["ret_5d"] = df["close"].pct_change(5)
    df["ret_20d"] = df["close"].pct_change(20)
    df["vol_20d"] = df["ret_1d"].rolling(20).std() * (252**0.5)

    print("  ✓ ret_1d: Daily returns")
    print("  ✓ ret_5d: 5-day returns")
    print("  ✓ ret_20d: 20-day returns")
    print("  ✓ vol_20d: 20-day annualized volatility")

    # Clean & write
    df.to_csv(OUT, index=False)

    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"\nOutput file: {OUT}")
    print(f"Total rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    print(f"\nColumns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    print("\n" + "="*80)
    print("Sample data (latest 5 rows):")
    print("="*80)
    display_cols = ['date', 'close', 'ret_1d', 'vol_20d']
    if 'gdd' in df.columns:
        display_cols.append('gdd')
    if 'condition_index' in df.columns:
        display_cols.append('condition_index')

    available_cols = [col for col in display_cols if col in df.columns]
    print(df[available_cols].tail(5).to_string(index=False))

    print("\n" + "="*80)
    print("[SUCCESS] SOYBEAN DATA MERGE COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review merged data: data/soybean_combined.csv")
    print("2. Use for model training and analysis")
    print("3. Compare with corn_combined.csv for cross-commodity insights")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
