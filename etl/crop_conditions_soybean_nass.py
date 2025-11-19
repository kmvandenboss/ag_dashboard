#!/usr/bin/env python3

import requests
import pandas as pd
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

# USDA NASS QuickStats API
# Documentation: https://quickstats.nass.usda.gov/api
# Your API key (from requirements document)
NASS_API_KEY = "27ED3F7D-193C-3B76-BC18-2BD66E747185"

BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
START_YEAR = 2005
OUT = "data/crop_conditions_soybean.csv"

def fetch_nass_data(params, description=""):
    """
    Fetch data from NASS QuickStats API
    """
    params['key'] = NASS_API_KEY
    params['format'] = 'JSON'

    print(f"  Fetching: {description}...")

    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            df = pd.DataFrame(data['data'])
            print(f"    Retrieved {len(df)} records")
            return df
        else:
            print(f"    No data returned")
            return pd.DataFrame()

    except requests.exceptions.HTTPError as e:
        print(f"    HTTP Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"    Error: {e}")
        return pd.DataFrame()

def fetch_crop_conditions():
    """
    Fetch weekly crop condition ratings
    Categories: EXCELLENT, GOOD, FAIR, POOR, VERY POOR
    """
    print("\n[1] Fetching Crop Condition Ratings...")

    params = {
        'source_desc': 'SURVEY',
        'commodity_desc': 'SOYBEANS',
        'statisticcat_desc': 'CONDITION',
        'agg_level_desc': 'NATIONAL',
        'freq_desc': 'WEEKLY',
        'year__GE': START_YEAR,
    }

    df = fetch_nass_data(params, "Crop conditions (EXCELLENT, GOOD, FAIR, POOR, VERY POOR)")

    if df.empty:
        return df

    # Clean and structure the data
    df['week_ending'] = pd.to_datetime(df['week_ending'])
    df['value'] = pd.to_numeric(df['Value'], errors='coerce')

    # The key field is 'short_desc' which contains condition ratings
    # Example: "SOYBEANS - CONDITION, MEASURED IN PCT EXCELLENT"
    # Extract the rating type from short_desc
    df['rating'] = df['short_desc'].str.extract(r'PCT (\w+(?:\s\w+)?)', expand=False)

    # Pivot by rating
    pivot = df.pivot_table(
        index='week_ending',
        columns='rating',
        values='value',
        aggfunc='first'
    ).reset_index()

    pivot.columns.name = None
    pivot = pivot.rename(columns={'week_ending': 'date'})

    return pivot

def fetch_crop_progress():
    """
    Fetch weekly crop progress metrics
    Stages: PLANTED, EMERGED, BLOOMING, SETTING PODS, DROPPING LEAVES, HARVESTED
    """
    print("\n[2] Fetching Crop Progress Metrics...")

    params = {
        'source_desc': 'SURVEY',
        'commodity_desc': 'SOYBEANS',
        'statisticcat_desc': 'PROGRESS',
        'agg_level_desc': 'NATIONAL',
        'freq_desc': 'WEEKLY',
        'year__GE': START_YEAR,
    }

    df = fetch_nass_data(params, "Crop progress (PLANTED, EMERGED, BLOOMING, etc.)")

    if df.empty:
        return df

    # Clean and structure
    df['week_ending'] = pd.to_datetime(df['week_ending'])
    df['value'] = pd.to_numeric(df['Value'], errors='coerce')

    # Extract progress stage from short_desc
    # Example: "SOYBEANS - PROGRESS, MEASURED IN PCT PLANTED"
    df['stage'] = df['short_desc'].str.extract(r'PCT (\w+(?:\s\w+)?)', expand=False)

    # Pivot by progress stage
    pivot = df.pivot_table(
        index='week_ending',
        columns='stage',
        values='value',
        aggfunc='first'
    ).reset_index()

    pivot.columns.name = None
    pivot = pivot.rename(columns={'week_ending': 'date'})

    return pivot

def fetch_state_weather():
    """
    Fetch state-level weather summaries from NASS weekly reports
    Includes: Growing Degree Days, Precipitation
    Note: This is less reliable than NOAA direct data
    """
    print("\n[3] Fetching State Weather Data (from weekly reports)...")

    # NASS doesn't have a direct weather API endpoint
    # This data comes from the weekly Crop Progress reports
    # For now, we'll skip this and rely on NOAA weather data instead

    print("  Skipping - using NOAA weather data instead")
    return pd.DataFrame()

def merge_crop_data(conditions_df, progress_df):
    """
    Merge condition and progress data into single dataset
    """
    if conditions_df.empty and progress_df.empty:
        return pd.DataFrame()

    if conditions_df.empty:
        return progress_df

    if progress_df.empty:
        return conditions_df

    # Merge on date
    merged = pd.merge(
        conditions_df,
        progress_df,
        on='date',
        how='outer',
        suffixes=('_condition', '_progress')
    )

    return merged

def clean_column_names(df):
    """
    Clean and standardize column names
    """
    # Convert to lowercase and replace spaces
    df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]

    # Standardize condition columns
    rename_map = {}

    if 'excellent' in df.columns:
        rename_map['excellent'] = 'pct_excellent'
    if 'good' in df.columns:
        rename_map['good'] = 'pct_good'
    if 'fair' in df.columns:
        rename_map['fair'] = 'pct_fair'
    if 'poor' in df.columns:
        rename_map['poor'] = 'pct_poor'
    if 'very_poor' in df.columns:
        rename_map['very_poor'] = 'pct_very_poor'

    # Standardize progress columns for soybeans
    if 'planted' in df.columns:
        rename_map['planted'] = 'pct_planted'
    if 'emerged' in df.columns:
        rename_map['emerged'] = 'pct_emerged'
    if 'blooming' in df.columns:
        rename_map['blooming'] = 'pct_blooming'
    if 'setting_pods' in df.columns:
        rename_map['setting_pods'] = 'pct_setting_pods'
    if 'dropping_leaves' in df.columns:
        rename_map['dropping_leaves'] = 'pct_dropping_leaves'
    if 'harvested' in df.columns:
        rename_map['harvested'] = 'pct_harvested'

    df = df.rename(columns=rename_map)

    return df

def add_derived_metrics(df):
    """
    Add derived crop condition metrics
    """
    # Good + Excellent percentage (bullish indicator when low)
    good_excellent_cols = [col for col in ['pct_good', 'pct_excellent'] if col in df.columns]
    if good_excellent_cols:
        df['pct_good_excellent'] = df[good_excellent_cols].sum(axis=1)

    # Poor + Very Poor percentage (bullish indicator when high)
    poor_cols = [col for col in ['pct_poor', 'pct_very_poor'] if col in df.columns]
    if poor_cols:
        df['pct_poor_very_poor'] = df[poor_cols].sum(axis=1)

    # Crop condition index (0-100 scale, higher = better conditions = bearish)
    if all(col in df.columns for col in ['pct_excellent', 'pct_good', 'pct_fair', 'pct_poor', 'pct_very_poor']):
        df['condition_index'] = (
            df['pct_excellent'] * 1.0 +
            df['pct_good'] * 0.75 +
            df['pct_fair'] * 0.5 +
            df['pct_poor'] * 0.25 +
            df['pct_very_poor'] * 0.0
        )

    return df

def main():
    print("="*80)
    print("FETCHING CROP CONDITIONS DATA FROM USDA NASS FOR SOYBEANS")
    print("="*80)
    print(f"\nData source: USDA NASS QuickStats API")
    print(f"Date range: {START_YEAR} to present")
    print(f"Coverage: National soybean crop conditions and progress")
    print(f"Frequency: Weekly reports during growing season (May-Nov)")
    print("="*80)

    # Fetch different data types
    conditions_df = fetch_crop_conditions()
    time.sleep(1)  # Rate limiting

    progress_df = fetch_crop_progress()
    time.sleep(1)

    # Merge datasets
    print("\nMerging condition and progress data...")
    df_crop = merge_crop_data(conditions_df, progress_df)

    if df_crop.empty:
        print("\nWARNING: No crop data retrieved from NASS API")
        print("This could be due to:")
        print("  - API key issues")
        print("  - Data not available for requested time period")
        print("  - API endpoint changes")
        print("\nCreating empty template file...")

        # Create empty template
        df_crop = pd.DataFrame(columns=['date'])

    # Clean column names
    df_crop = clean_column_names(df_crop)

    # Add derived metrics
    if not df_crop.empty and 'pct_excellent' in df_crop.columns:
        print("Calculating derived metrics...")
        df_crop = add_derived_metrics(df_crop)

    # Sort and save
    if not df_crop.empty:
        df_crop = df_crop.sort_values('date').reset_index(drop=True)

    df_crop.to_csv(OUT, index=False)

    print(f"\n{'='*80}")
    print("CROP CONDITIONS DATA SAVED")
    print('='*80)
    print(f"Output: {OUT}")
    print(f"Rows: {len(df_crop):,}")

    if not df_crop.empty:
        print(f"Date range: {df_crop['date'].min()} to {df_crop['date'].max()}")
        print(f"Columns ({len(df_crop.columns)}): {list(df_crop.columns)}")

        print("\nSample data (latest 5 weeks):")
        display_cols = [col for col in ['date', 'pct_excellent', 'pct_good', 'pct_fair', 'pct_planted', 'pct_harvested'] if col in df_crop.columns]
        if display_cols:
            print(df_crop.tail(5)[display_cols].to_string(index=False))

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
