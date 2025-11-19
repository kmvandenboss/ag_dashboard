#!/usr/bin/env python3
"""
Open-Meteo Weather Data Fetcher for Corn Belt
Real-time weather data with only 2-day lag (vs months for NOAA nClimGrid)

Data Source: https://open-meteo.com/en/docs/historical-weather-api
- Free for non-commercial use, no API key required
- Historical data from 1940-present with 2-day lag
- Hourly data aggregated to daily
- 10km resolution

This script fetches recent weather data and appends to existing files,
allowing us to keep NOAA historical data (2005-Aug 2025) and use
Open-Meteo for current/recent data (Sep 2025-present).

Usage:
  python etl/weather_openmeteo.py              # Fetch from last available date to yesterday
  python etl/weather_openmeteo.py --backfill   # Fetch from 2024-01-01 to yesterday
  python etl/weather_openmeteo.py --start 2025-09-01  # Fetch from specific date
"""

import sys
import io
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
API_BASE = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_CORN = "data/weather_corn_belt_index.csv"
OUTPUT_SOY = "data/weather_soybean_belt_index.csv"

# Corn Belt Representative Coordinates (production-weighted centers)
# Format: (latitude, longitude, weight, state_name)
CORN_BELT_LOCATIONS = [
    (42.03, -93.62, 0.274, "Iowa"),          # Iowa - Des Moines area
    (40.11, -88.24, 0.228, "Illinois"),      # Illinois - Champaign area
    (41.49, -99.90, 0.213, "Nebraska"),      # Nebraska - Grand Island area
    (44.95, -93.09, 0.137, "Minnesota"),     # Minnesota - Twin Cities area
    (40.27, -86.13, 0.106, "Indiana"),       # Indiana - Lafayette area
    (40.42, -82.91, 0.061, "Ohio"),          # Ohio - Columbus area
]

# Soybean Belt (similar but slightly different weights)
SOYBEAN_BELT_LOCATIONS = [
    (40.11, -88.24, 0.230, "Illinois"),      # Illinois - Champaign area
    (42.03, -93.62, 0.227, "Iowa"),          # Iowa - Des Moines area
    (44.95, -93.09, 0.145, "Minnesota"),     # Minnesota - Twin Cities area
    (40.27, -86.13, 0.124, "Indiana"),       # Indiana - Lafayette area
    (41.49, -99.90, 0.141, "Nebraska"),      # Nebraska - Grand Island area
    (39.96, -82.99, 0.075, "Ohio"),          # Ohio - Columbus area
    (38.57, -92.60, 0.058, "Missouri"),      # Missouri - Columbia area
]


def fetch_location_weather(lat, lon, start_date, end_date, location_name):
    """
    Fetch weather data for a single location from Open-Meteo

    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        location_name: Name for logging

    Returns:
        DataFrame with daily weather data
    """
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date,
        'daily': [
            'temperature_2m_max',
            'temperature_2m_min',
            'temperature_2m_mean',
            'precipitation_sum',
        ],
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'timezone': 'America/Chicago',
    }

    try:
        response = requests.get(API_BASE, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'daily' not in data:
            print(f"  ⚠ No daily data returned for {location_name}")
            return None

        df = pd.DataFrame({
            'date': pd.to_datetime(data['daily']['time']),
            'tmax': data['daily']['temperature_2m_max'],
            'tmin': data['daily']['temperature_2m_min'],
            'tavg': data['daily']['temperature_2m_mean'],
            'prcp': data['daily']['precipitation_sum'],
        })

        return df

    except Exception as e:
        print(f"  ✗ Error fetching {location_name}: {e}")
        return None


def fetch_belt_weather(locations, start_date, end_date, belt_name="Corn Belt"):
    """
    Fetch weather data for all locations in the belt and compute weighted average

    Args:
        locations: List of (lat, lon, weight, name) tuples
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        belt_name: Name for logging

    Returns:
        DataFrame with weighted daily weather indices
    """
    print(f"\nFetching {belt_name} Weather Data")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Locations: {len(locations)}")
    print("="*80)

    all_data = []

    for lat, lon, weight, name in locations:
        print(f"  Fetching {name} (weight: {weight:.1%})...", end=" ")
        df = fetch_location_weather(lat, lon, start_date, end_date, name)

        if df is not None and len(df) > 0:
            df['weight'] = weight
            df['location'] = name
            all_data.append(df)
            print(f"✓ {len(df)} days")
        else:
            print("✗ Failed")

        # Be nice to the API
        time.sleep(0.1)

    if not all_data:
        print("\n⚠ No data fetched!")
        return None

    # Combine all location data
    df_all = pd.concat(all_data, ignore_index=True)

    # Calculate weighted averages by date
    print(f"\nCalculating weighted {belt_name.lower()} indices...")
    df_weighted = df_all.groupby('date').apply(
        lambda x: pd.Series({
            'tmax': (x['tmax'] * x['weight']).sum(),
            'tmin': (x['tmin'] * x['weight']).sum(),
            'tavg': (x['tavg'] * x['weight']).sum(),
            'prcp': (x['prcp'] * x['weight']).sum(),
        })
    ).reset_index()

    # Calculate derived metrics
    print("Calculating derived metrics...")

    # GDD (Growing Degree Days) - base 50°F
    df_weighted['gdd'] = df_weighted['tavg'].apply(lambda x: max(0, x - 50))

    # Cumulative GDD (reset each year)
    df_weighted['year'] = df_weighted['date'].dt.year
    df_weighted['gdd_cumulative'] = df_weighted.groupby('year')['gdd'].cumsum()
    df_weighted = df_weighted.drop('year', axis=1)

    # Temperature anomaly (30-day rolling mean)
    df_weighted['tavg_30d_ma'] = df_weighted['tavg'].rolling(30, min_periods=15).mean()
    df_weighted['tavg_anomaly'] = df_weighted['tavg'] - df_weighted['tavg_30d_ma']

    # Precipitation anomaly (30-day rolling)
    df_weighted['prcp_30d_ma'] = df_weighted['prcp'].rolling(30, min_periods=15).mean()
    df_weighted['prcp_anomaly'] = df_weighted['prcp'] - df_weighted['prcp_30d_ma']

    # Heat stress (days > 86°F during growing season)
    df_weighted['heat_stress'] = (df_weighted['tmax'] > 86).astype(int)

    # Dry days (< 0.01" precipitation)
    df_weighted['dry_day'] = (df_weighted['prcp'] < 0.01).astype(int)

    # Rolling precipitation totals
    df_weighted['prcp_7d'] = df_weighted['prcp'].rolling(7, min_periods=1).sum()
    df_weighted['prcp_30d'] = df_weighted['prcp'].rolling(30, min_periods=1).sum()

    # Drop intermediate columns
    df_weighted = df_weighted.drop(['tavg_30d_ma', 'prcp_30d_ma'], axis=1)

    print(f"  ✓ {len(df_weighted)} days of weighted indices calculated")

    return df_weighted


def merge_with_existing(new_data, output_file, belt_name="Corn Belt"):
    """
    Merge new data with existing historical data

    Args:
        new_data: DataFrame with new weather data
        output_file: Path to existing CSV file
        belt_name: Name for logging
    """
    try:
        existing = pd.read_csv(output_file, parse_dates=['date'])
        print(f"\nExisting {belt_name} data:")
        print(f"  Rows: {len(existing)}")
        print(f"  Date range: {existing['date'].min().date()} to {existing['date'].max().date()}")

        # Find overlap
        overlap_start = max(existing['date'].min(), new_data['date'].min())
        overlap_end = min(existing['date'].max(), new_data['date'].max())

        if overlap_start <= overlap_end:
            print(f"\n  Overlap detected: {overlap_start.date()} to {overlap_end.date()}")
            print(f"  Removing overlapping dates from existing data...")
            existing = existing[existing['date'] < new_data['date'].min()]

        # Combine
        combined = pd.concat([existing, new_data], ignore_index=True)
        combined = combined.sort_values('date').reset_index(drop=True)

        # Recalculate cumulative metrics across the entire dataset
        print("  Recalculating cumulative metrics...")
        combined['year'] = combined['date'].dt.year
        combined['gdd_cumulative'] = combined.groupby('year')['gdd'].cumsum()
        combined = combined.drop('year', axis=1)

        print(f"\nCombined {belt_name} data:")
        print(f"  Rows: {len(combined)}")
        print(f"  Date range: {combined['date'].min().date()} to {combined['date'].max().date()}")
        print(f"  New rows added: {len(combined) - len(existing)}")

        return combined

    except FileNotFoundError:
        print(f"\n⚠ {output_file} not found - creating new file")
        return new_data


def main():
    parser = argparse.ArgumentParser(description='Fetch weather data from Open-Meteo')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD), defaults to yesterday')
    parser.add_argument('--backfill', action='store_true', help='Backfill from 2024-01-01')
    parser.add_argument('--corn-only', action='store_true', help='Only update corn belt data')
    parser.add_argument('--soy-only', action='store_true', help='Only update soybean belt data')

    args = parser.parse_args()

    # Determine date range
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    if args.backfill:
        start_date = '2024-01-01'
        end_date = yesterday
    elif args.start:
        start_date = args.start
        end_date = args.end if args.end else yesterday
    else:
        # Auto-detect: fetch from last date in existing file + 1 day
        try:
            existing = pd.read_csv(OUTPUT_CORN, parse_dates=['date'])
            last_date = existing['date'].max()
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = yesterday
            print(f"Auto-detected start date: {start_date} (last date in file: {last_date.date()})")
        except FileNotFoundError:
            start_date = '2024-01-01'
            end_date = yesterday
            print(f"No existing file found - starting from {start_date}")

    print("="*80)
    print("OPEN-METEO WEATHER DATA UPDATE")
    print("="*80)
    print(f"Period: {start_date} to {end_date}")
    print(f"Source: Open-Meteo Historical Weather API")
    print(f"Lag: ~2 days (vs months for NOAA)")
    print("="*80)

    # Fetch corn belt data
    if not args.soy_only:
        df_corn = fetch_belt_weather(CORN_BELT_LOCATIONS, start_date, end_date, "Corn Belt")

        if df_corn is not None and len(df_corn) > 0:
            # Merge with existing
            df_corn_final = merge_with_existing(df_corn, OUTPUT_CORN, "Corn Belt")

            # Save
            df_corn_final.to_csv(OUTPUT_CORN, index=False)
            print(f"\n✓ Saved to {OUTPUT_CORN}")
        else:
            print("\n✗ No corn belt data to save")

    # Fetch soybean belt data
    if not args.corn_only:
        df_soy = fetch_belt_weather(SOYBEAN_BELT_LOCATIONS, start_date, end_date, "Soybean Belt")

        if df_soy is not None and len(df_soy) > 0:
            # Merge with existing
            df_soy_final = merge_with_existing(df_soy, OUTPUT_SOY, "Soybean Belt")

            # Save
            df_soy_final.to_csv(OUTPUT_SOY, index=False)
            print(f"\n✓ Saved to {OUTPUT_SOY}")
        else:
            print("\n✗ No soybean belt data to save")

    print("\n" + "="*80)
    print("WEATHER DATA UPDATE COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Run merge scripts to update combined datasets")
    print("2. Set up daily cron job: python etl/weather_openmeteo.py")
    print("   (Will auto-fetch from last date to yesterday)")
    print("="*80)


if __name__ == "__main__":
    main()
