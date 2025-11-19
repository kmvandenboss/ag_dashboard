#!/usr/bin/env python3
"""
MASTER DATA UPDATE PIPELINE
============================

Runs the complete data update pipeline for both corn and soybean models:
1. Fetch latest price data
2. Update other data sources (COT, weather, etc.)
3. Merge all data sources
4. Run feature engineering
5. Verify data quality

Usage:
    python update_pipeline.py              # Update both corn and soybeans
    python update_pipeline.py --corn-only  # Update only corn
    python update_pipeline.py --soy-only   # Update only soybeans
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Change to project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print(f"\n[RUNNING] {description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
            return True
        else:
            print(f"[ERROR] {description} failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[ERROR] {description} timed out")
        return False
    except Exception as e:
        print(f"[ERROR] {description} failed: {e}")
        return False

def verify_data(asset):
    """Verify that data was updated successfully"""
    print(f"\n[VERIFY] Checking {asset} data...")
    try:
        import pandas as pd

        features_file = f'data/{asset}_combined_features.csv'
        df = pd.read_csv(features_file, parse_dates=['date'])

        latest_date = df['date'].max()
        latest_price = df.iloc[-1]['close']
        today = datetime.now().date()

        print(f"  Total rows: {len(df)}")
        print(f"  Latest date: {latest_date.date()}")
        print(f"  Latest price: ${latest_price:.2f}")

        # Check if data is recent (within 5 days)
        days_old = (today - latest_date.date()).days
        if days_old > 5:
            print(f"  [WARNING] Data is {days_old} days old")
            return False
        else:
            print(f"  [OK] Data is current ({days_old} days old)")
            return True

    except Exception as e:
        print(f"  [ERROR] Verification failed: {e}")
        return False

def update_corn():
    """Update corn data pipeline"""
    print_header("UPDATING CORN DATA")

    steps = [
        # Step 1: Fetch latest prices
        ("etl/corn_prices_yahoo.py", "Fetch corn prices"),

        # Step 2: Update data sources (only if needed - these update less frequently)
        # Uncomment if you need to update these:
        # ("etl/cot_corn_cftc.py", "Update COT data"),
        # ("etl/cftc_options_corn.py", "Update CFTC options"),
        # ("etl/wasde_corn_usda.py", "Update WASDE data"),
        # ("etl/crop_conditions_nass.py", "Update crop conditions"),
        # ("etl/weather_openmeteo.py", "Update weather data (corn)"),

        # Step 3: Merge all data sources
        ("etl/merge_corn_wrapper.py", "Merge corn data sources"),

        # Step 4: Feature engineering
        ("features/corn_features.py", "Generate corn features"),
    ]

    success = True
    for script, description in steps:
        if not run_script(script, description):
            success = False
            break

    if success:
        verify_data('corn')

    return success

def update_soybean():
    """Update soybean data pipeline"""
    print_header("UPDATING SOYBEAN DATA")

    steps = [
        # Step 1: Fetch latest prices
        ("etl/soybean_prices_yahoo.py", "Fetch soybean prices"),

        # Step 2: Update data sources (only if needed - these update less frequently)
        # Uncomment if you need to update these:
        # ("etl/cot_soybean_cftc.py", "Update COT data"),
        # ("etl/cftc_options_soybean.py", "Update CFTC options"),
        # ("etl/wasde_soybean_usda.py", "Update WASDE data"),
        # ("etl/crop_conditions_soybean_nass.py", "Update crop conditions"),
        # ("etl/weather_openmeteo.py", "Update weather data (soybean)"),

        # Step 3: Merge all data sources
        ("etl/merge_soybean_wrapper.py", "Merge soybean data sources"),

        # Step 4: Feature engineering
        ("features/soybean_features.py", "Generate soybean features"),
    ]

    success = True
    for script, description in steps:
        if not run_script(script, description):
            success = False
            break

    if success:
        verify_data('soybean')

    return success

def main():
    """Main pipeline execution"""
    start_time = datetime.now()

    print_header(f"AG ANALYST DATA UPDATE PIPELINE - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Parse command line arguments
    corn_only = '--corn-only' in sys.argv
    soy_only = '--soy-only' in sys.argv

    results = {}

    # Run updates
    if not soy_only:
        results['corn'] = update_corn()

    if not corn_only:
        results['soybean'] = update_soybean()

    # Print summary
    print_header("PIPELINE SUMMARY")

    for asset, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {asset.capitalize()}: {status}")

    elapsed = datetime.now() - start_time
    print(f"\nTotal time: {elapsed.total_seconds():.1f} seconds")

    # Exit with error code if any failed
    if not all(results.values()):
        print("\n[ERROR] Some updates failed. Check logs above.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All updates completed successfully!")
        print("\nNext steps:")
        print("  1. Restart Streamlit dashboard (if running) to see updated data")
        print("  2. Run: python scripts/generate_signals.py")
        sys.exit(0)

if __name__ == "__main__":
    main()
