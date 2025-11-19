#!/usr/bin/env python3
import pandas as pd
from dateutil.relativedelta import relativedelta

PRICES = "data/corn_prices.csv"
COT = "data/cot_corn.csv"
CFTC_OPTIONS = "data/cftc_options_corn.csv"
WASDE = "data/wasde_corn.csv"
CROP_CONDITIONS = "data/crop_conditions.csv"
WEATHER_INDEX = "data/weather_corn_belt_index.csv"
CURRENCY = "data/currency_data.csv"
OUT = "data/corn_combined.csv"

def main():
    prices = pd.read_csv(PRICES, parse_dates=["date"])
    cot = pd.read_csv(COT, parse_dates=["date"])
    # Remove rows with NaT dates, duplicate dates, then sort
    cot = cot.dropna(subset=["date"])
    cot = cot.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    # Forward-fill weekly COT to daily for merging on calendar days
    cot_indexed = cot.set_index("date")
    cot_daily = cot_indexed.reindex(pd.date_range(cot_indexed.index.min(), cot_indexed.index.max(), freq="D"))
    cot_daily = cot_daily.ffill().reset_index().rename(columns={"index": "date"})

    # WASDE monthly; we forward-fill daily as well
    wasde = pd.read_csv(WASDE, parse_dates=["date"])
    wasde = wasde.dropna(subset=["date"])
    wasde = wasde.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    if len(wasde) > 0:
        wasde_indexed = wasde.set_index("date")
        wasde_daily = wasde_indexed.reindex(pd.date_range(wasde_indexed.index.min(), wasde_indexed.index.max(), freq="D"))
        wasde_daily = wasde_daily.ffill().reset_index().rename(columns={"index": "date"})
    else:
        wasde_daily = wasde  # Empty dataframe

    # Crop conditions weekly; forward-fill to daily
    crop_conditions = pd.read_csv(CROP_CONDITIONS, parse_dates=["date"])
    crop_conditions = crop_conditions.dropna(subset=["date"])
    crop_conditions = crop_conditions.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    if len(crop_conditions) > 0:
        crop_indexed = crop_conditions.set_index("date")
        crop_daily = crop_indexed.reindex(pd.date_range(crop_indexed.index.min(), crop_indexed.index.max(), freq="D"))
        crop_daily = crop_daily.ffill().reset_index().rename(columns={"index": "date"})
    else:
        crop_daily = crop_conditions  # Empty dataframe

    # CFTC Options data (futures+options combined); weekly, forward-fill to daily
    try:
        cftc_options = pd.read_csv(CFTC_OPTIONS, parse_dates=["date"])
        cftc_options = cftc_options.dropna(subset=["date"])
        cftc_options = cftc_options.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
        if len(cftc_options) > 0:
            options_indexed = cftc_options.set_index("date")
            options_daily = options_indexed.reindex(pd.date_range(options_indexed.index.min(), options_indexed.index.max(), freq="D"))
            options_daily = options_daily.ffill().reset_index().rename(columns={"index": "date"})
        else:
            options_daily = cftc_options
    except FileNotFoundError:
        print(f"Warning: {CFTC_OPTIONS} not found. Skipping CFTC options data.")
        options_daily = pd.DataFrame()

    # Weather index (daily + monthly combined); already in daily format with forward-filled monthly data
    try:
        weather = pd.read_csv(WEATHER_INDEX, parse_dates=["date"])
        weather = weather.dropna(subset=["date"])
        weather = weather.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    except FileNotFoundError:
        print(f"Warning: {WEATHER_INDEX} not found. Skipping weather data.")
        weather = pd.DataFrame()

    # Currency data - DISABLED (kept in currency_data.csv for future analysis)
    # To re-enable: uncomment the lines below
    # try:
    #     currency = pd.read_csv(CURRENCY, parse_dates=["date"])
    #     currency = currency.dropna(subset=["date"])
    #     currency = currency.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    #     print(f"Loaded currency data: {len(currency):,} rows")
    # except FileNotFoundError:
    #     print(f"Warning: {CURRENCY} not found. Skipping currency data.")
    #     currency = pd.DataFrame()

    # Merge all datasets
    df = prices.merge(cot_daily, on="date", how="left")
    df = df.merge(wasde_daily, on="date", how="left")
    df = df.merge(crop_daily, on="date", how="left")

    if len(options_daily) > 0:
        df = df.merge(options_daily, on="date", how="left")

    if len(weather) > 0:
        df = df.merge(weather, on="date", how="left")

    # Currency merge disabled - uncomment below to re-enable
    # if len(currency) > 0:
    #     df = df.merge(currency, on="date", how="left")
    #     # Forward-fill currency data for any missing dates (though should be minimal)
    #     currency_cols = [col for col in df.columns if col.startswith(('dxy_', 'usd_', 'competitiveness_'))]
    #     df[currency_cols] = df[currency_cols].ffill()
    #     print(f"Merged currency data: {len(currency_cols)} currency columns added")

    # Derived metrics
    df["ret_1d"] = df["close"].pct_change()
    df["ret_5d"] = df["close"].pct_change(5)
    df["ret_20d"] = df["close"].pct_change(20)
    df["vol_20d"] = df["ret_1d"].rolling(20).std() * (252**0.5)

    # Clean & write
    df.to_csv(OUT, index=False)
    print("Wrote", OUT, "rows:", len(df))

if __name__ == "__main__":
    main()
