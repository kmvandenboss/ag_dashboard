#!/usr/bin/env python3

import requests
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# USDA ERS Feed Grains Yearbook Tables
# Data source: https://www.ers.usda.gov/data-products/feed-grains-database/feed-grains-yearbook-tables/
# Contains historical and recent corn data including production, yield, stocks, and exports
# Note: This data represents USDA's revised estimates, not original WASDE published values

START_YEAR = 2005
OUT = "data/wasde_corn.csv"

# ERS Feed Grains Yearbook URLs
HISTORICAL_URL = "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/50048/feed-grains-yearbook-historical.csv"
RECENT_URL = "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/50048/feed-grains-yearbook-recent.csv"

def fetch_ers_data(url):
    """
    Fetch ERS Feed Grains data from CSV URL
    """
    print(f"Fetching {url.split('/')[-1]}...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(pd.io.common.StringIO(r.text))
    return df

def extract_corn_data(df, start_year=START_YEAR):
    """
    Extract corn-specific data for yield, production, ending stocks, and exports
    Returns a dictionary with each metric
    """
    # Filter for corn commodity only
    corn = df[df['commodity'] == 'Corn'].copy()

    # Filter for years >= start_year
    corn = corn[corn['year'] >= start_year]

    # Standardize unit to million bushels (filter out metric tons)
    corn = corn[corn['unit'] == 'Million bushels']

    data = {}

    # 1. Yield (annual only, bushels per acre)
    # Note: Yield uses different unit, so we need to handle it separately
    yield_df = df[
        (df['commodity'] == 'Corn') &
        (df['attribute'] == 'Yield per harvested acre') &
        (df['unit'] == 'Bushels per acre') &
        (df['frequency'] == 'Annual') &
        (df['year'] >= start_year)
    ][['year', 'amount']].copy()
    yield_df.columns = ['year', 'yield_estimate_bu_per_acre']
    data['yield'] = yield_df

    # 2. Production (annual only)
    prod_df = corn[
        (corn['attribute'] == 'Production') &
        (corn['frequency'] == 'Annual')
    ][['year', 'amount']].copy()
    prod_df.columns = ['year', 'production_mbu']
    data['production'] = prod_df

    # 3. Ending Stocks (quarterly - we'll use Q4/end of marketing year)
    # Marketing year for corn is Sep-Aug, so Q4 ending stocks = August ending stocks
    stocks_df = corn[
        (corn['attribute'] == 'Ending stocks') &
        (corn['frequency'] == 'Quarterly')
    ].copy()

    # Parse timeperiod to get quarter
    # Timeperiod format examples: "Sep-Nov", "Dec-Feb", "Mar-May", "Jun-Aug"
    stocks_df['quarter'] = stocks_df['timeperiod'].apply(lambda x: x.split('-')[1] if '-' in str(x) else '')

    # For each year, take the last quarter (Aug ending = end of marketing year)
    stocks_df = stocks_df[stocks_df['quarter'] == 'Aug'][['year', 'amount']].copy()
    stocks_df.columns = ['year', 'ending_stocks_mbu']
    data['stocks'] = stocks_df

    # 4. Exports (annual)
    exports_df = corn[
        (corn['attribute'] == 'Exports') &
        (corn['frequency'] == 'Annual')
    ][['year', 'amount']].copy()
    exports_df.columns = ['year', 'exports_mbu']
    data['exports'] = exports_df

    return data

def merge_annual_data(data_dict):
    """
    Merge all annual data into a single DataFrame
    """
    # Start with yield (most complete annual data)
    result = data_dict['yield'].drop_duplicates(subset=['year'])

    # Merge each metric
    for key in ['production', 'stocks', 'exports']:
        if key in data_dict and not data_dict[key].empty:
            # Remove duplicates before merging
            df_clean = data_dict[key].drop_duplicates(subset=['year'])
            result = result.merge(df_clean, on='year', how='outer')

    return result.sort_values('year')

def expand_to_monthly(df_annual):
    """
    Expand annual data to monthly with carry-forward logic
    Each year's values repeat for all 12 months
    """
    monthly_rows = []

    for _, row in df_annual.iterrows():
        year = int(row['year'])
        for month in range(1, 13):
            date = f"{year}-{month:02d}-01"
            monthly_row = {'date': date}

            # Add all other columns
            for col in df_annual.columns:
                if col != 'year':
                    monthly_row[col] = row[col]

            monthly_rows.append(monthly_row)

    df_monthly = pd.DataFrame(monthly_rows)
    df_monthly['date'] = pd.to_datetime(df_monthly['date'])

    # Add notes column (empty for now)
    df_monthly['notes'] = ''

    return df_monthly

def validate_and_clean(df):
    """
    Validate output format and clean data
    """
    required_cols = [
        'date',
        'yield_estimate_bu_per_acre',
        'production_mbu',
        'ending_stocks_mbu',
        'exports_mbu',
        'notes'
    ]

    # Ensure all required columns exist
    for col in required_cols:
        if col not in df.columns:
            print(f"Warning: Missing column {col}, adding with NaN values")
            df[col] = pd.NA

    # Reorder columns
    df = df[required_cols]

    # Log missing data
    for col in required_cols[1:-1]:  # Skip date and notes
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            print(f"Warning: {missing_count} missing values in {col}")
            missing_years = df[df[col].isna()]['date'].dt.year.unique()
            if len(missing_years) > 0:
                print(f"  Missing years: {sorted(missing_years)}")

    return df

def main():
    print(f"Fetching WASDE corn data from {START_YEAR} to present")
    print("Source: USDA ERS Feed Grains Yearbook Tables")
    print("Note: This data contains revised estimates, not original published WASDE values\n")

    # Fetch both historical and recent data
    frames = []
    for url in [HISTORICAL_URL, RECENT_URL]:
        try:
            df = fetch_ers_data(url)
            frames.append(df)
        except Exception as e:
            print(f"Warning: Failed to fetch {url.split('/')[-1]}: {e}")

    if not frames:
        raise SystemExit("Error: No data fetched from ERS")

    # Combine all data
    df_all = pd.concat(frames, ignore_index=True)
    print(f"Total rows fetched: {len(df_all)}\n")

    # Extract corn-specific metrics
    print("Extracting corn data (yield, production, stocks, exports)...")
    data_dict = extract_corn_data(df_all, start_year=START_YEAR)

    # Show data availability
    print(f"\nData availability:")
    for key, df in data_dict.items():
        if not df.empty:
            print(f"  {key}: {len(df)} years ({df['year'].min():.0f}-{df['year'].max():.0f})")
        else:
            print(f"  {key}: NO DATA")

    # Merge annual data
    print("\nMerging annual data...")
    df_annual = merge_annual_data(data_dict)
    print(f"Annual dataset: {len(df_annual)} years")

    # Expand to monthly with carry-forward
    print("Expanding to monthly data with carry-forward logic...")
    df_monthly = expand_to_monthly(df_annual)

    # Validate and clean
    df_monthly = validate_and_clean(df_monthly)

    # Save to CSV
    df_monthly.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    print(f"Total rows: {len(df_monthly)}")
    print(f"Date range: {df_monthly['date'].min()} to {df_monthly['date'].max()}")

    # Show sample
    print("\nSample data (first 5 rows):")
    print(df_monthly.head())

    print("\n" + "="*60)
    print("SUCCESS: WASDE data automation complete!")
    print("="*60)

if __name__ == "__main__":
    main()
