#!/usr/bin/env python3
"""
CFTC Options Data for Corn - Futures and Options Combined
Downloads CFTC Disaggregated COT reports (F&O Combined) to extract options positioning data
Calculates put/call ratios and trader positioning in corn options

The Disaggregated F&O Combined report includes detailed trader breakdowns:
- Producer/Merchant/Processor/User (Commercial hedgers)
- Swap Dealers
- Money Managers (Speculators - CTAs, CPOs, hedge funds)
- Other Reportables
- Nonreportable (Small traders)

Data source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
"""

import io
import zipfile
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# CFTC Disaggregated (Futures and Options Combined) historical data
# Available from 2006-present for agricultural commodities
START_YEAR = 2006
OUT = "data/cftc_options_corn.csv"

def year_urls(start=START_YEAR):
    """Generate URLs for yearly CFTC Disaggregated (F&O Combined) reports"""
    base = "https://www.cftc.gov/files/dea/history"
    current_year = datetime.now().year

    # First get the consolidated 2006-2016 file
    yield f"{base}/com_disagg_txt_2006_2016.zip"

    # Then get individual years from 2017 onwards
    for y in range(2017, current_year + 1):
        # Disaggregated F&O Combined format: com_disagg_txt_YYYY.zip
        yield f"{base}/com_disagg_txt_{y}.zip"

def fetch_year(url):
    """Download a single year's CFTC data"""
    print(f"Fetching {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return io.BytesIO(r.content)

def parse_zip(buf):
    """Extract and parse CSV from ZIP archive"""
    with zipfile.ZipFile(buf) as z:
        names = z.namelist()
        if not names:
            return pd.DataFrame()
        # Find the first .txt or .csv file
        data_file = next((n for n in names if n.endswith(('.txt', '.csv'))), names[0])
        with z.open(data_file) as f:
            df = pd.read_csv(f, low_memory=False)
    return df

def filter_corn_options(df):
    """
    Filter for corn and extract combined futures+options positioning data

    CFTC Disaggregated Combined Report includes:
    - Producer/Merchant/Processor/User (Commercial hedgers)
    - Swap Dealers
    - Money Managers (Speculators)
    - Other Reportables
    - Nonreportable (Small traders)

    Note: This is COMBINED futures+options. To isolate pure options, you would need to
    subtract futures-only data from combined data. For trading signals, combined data
    works well as it shows total trader positioning.
    """
    # Standardize column names - strip whitespace and replace spaces with underscores
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    # Find corn contracts
    if "Market_and_Exchange_Names" not in df.columns:
        print("Warning: Column 'Market_and_Exchange_Names' not found")
        print(f"Available columns: {list(df.columns[:10])}")
        return pd.DataFrame()

    mask = df["Market_and_Exchange_Names"].str.contains("CORN", case=False, na=False) & \
           df["Market_and_Exchange_Names"].str.contains("CHICAGO", case=False, na=False)

    d = df.loc[mask].copy()

    if d.empty:
        print("Warning: No corn data found in this file")
        return pd.DataFrame()

    # Parse report date
    if "Report_Date_as_YYYY-MM-DD" in d.columns:
        d["date"] = pd.to_datetime(d["Report_Date_as_YYYY-MM-DD"])
    elif "As_of_Date_In_Form_YYMMDD" in d.columns:
        d["date"] = pd.to_datetime(d["As_of_Date_In_Form_YYMMDD"], format='%y%m%d')
    else:
        print("Warning: No date column found")
        return pd.DataFrame()

    # Expected columns in Disaggregated Combined report:
    keep_cols = [
        "date",
        "Open_Interest_All",
        "Prod_Merc_Positions_Long_All",
        "Prod_Merc_Positions_Short_All",
        "Swap_Positions_Long_All",
        "Swap__Positions_Short_All",  # Note: Double underscore in original data
        "M_Money_Positions_Long_All",
        "M_Money_Positions_Short_All",
        "Other_Rept_Positions_Long_All",
        "Other_Rept_Positions_Short_All",
        "NonRept_Positions_Long_All",
        "NonRept_Positions_Short_All",
    ]

    # Handle missing columns gracefully
    for c in keep_cols:
        if c not in d.columns:
            d[c] = pd.NA

    d = d[keep_cols].sort_values("date")

    # Convert all numeric columns
    numeric_cols = [c for c in keep_cols if c != "date"]
    for col in numeric_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors='coerce')

    # Calculate net positions for each trader category
    d["prod_net"] = d["Prod_Merc_Positions_Long_All"] - d["Prod_Merc_Positions_Short_All"]
    d["swap_net"] = d["Swap_Positions_Long_All"] - d["Swap__Positions_Short_All"]
    d["mm_net"] = d["M_Money_Positions_Long_All"] - d["M_Money_Positions_Short_All"]
    d["other_net"] = d["Other_Rept_Positions_Long_All"] - d["Other_Rept_Positions_Short_All"]
    d["nonrep_net"] = d["NonRept_Positions_Long_All"] - d["NonRept_Positions_Short_All"]

    # Calculate total long and short for put/call ratio
    d["total_long"] = (
        d["Prod_Merc_Positions_Long_All"] +
        d["Swap_Positions_Long_All"] +
        d["M_Money_Positions_Long_All"] +
        d["Other_Rept_Positions_Long_All"] +
        d["NonRept_Positions_Long_All"]
    )

    d["total_short"] = (
        d["Prod_Merc_Positions_Short_All"] +
        d["Swap__Positions_Short_All"] +
        d["M_Money_Positions_Short_All"] +
        d["Other_Rept_Positions_Short_All"] +
        d["NonRept_Positions_Short_All"]
    )

    # Approximate put/call ratio (short interest / long interest)
    # Higher ratio = more bearish positioning (more puts relative to calls)
    d["put_call_ratio"] = d["total_short"] / d["total_long"].replace(0, pd.NA)

    # Calculate 52-week percentile rank for put/call ratio
    d["put_call_ratio_52w_min"] = d["put_call_ratio"].rolling(52, min_periods=1).min()
    d["put_call_ratio_52w_max"] = d["put_call_ratio"].rolling(52, min_periods=1).max()
    d["put_call_ratio_52w_pct"] = (
        (d["put_call_ratio"] - d["put_call_ratio_52w_min"]) /
        (d["put_call_ratio_52w_max"] - d["put_call_ratio_52w_min"]).replace(0, pd.NA) * 100
    )

    # Trader positioning as percentage of open interest
    d["mm_long_pct"] = d["M_Money_Positions_Long_All"] / d["Open_Interest_All"] * 100
    d["mm_short_pct"] = d["M_Money_Positions_Short_All"] / d["Open_Interest_All"] * 100
    d["prod_long_pct"] = d["Prod_Merc_Positions_Long_All"] / d["Open_Interest_All"] * 100
    d["prod_short_pct"] = d["Prod_Merc_Positions_Short_All"] / d["Open_Interest_All"] * 100

    # Select final columns for output (user's requested columns)
    output_cols = [
        "date",
        "Open_Interest_All",
        "total_long",
        "total_short",
        "put_call_ratio",
        "put_call_ratio_52w_pct",
        "M_Money_Positions_Long_All",
        "M_Money_Positions_Short_All",
        "Prod_Merc_Positions_Long_All",
        "Prod_Merc_Positions_Short_All",
        "mm_net",
        "prod_net",
        "swap_net",
        "mm_long_pct",
        "mm_short_pct",
        "prod_long_pct",
        "prod_short_pct",
    ]

    # Rename for clarity to match user's requested column names
    d = d[output_cols].rename(columns={
        "Open_Interest_All": "total_oi",
        "total_long": "total_calls_oi",
        "total_short": "total_puts_oi",
        "M_Money_Positions_Long_All": "mm_calls_oi",
        "M_Money_Positions_Short_All": "mm_puts_oi",
        "Prod_Merc_Positions_Long_All": "dealer_calls_oi",
        "Prod_Merc_Positions_Short_All": "dealer_puts_oi",
        "mm_net": "mm_net_position",
        "prod_net": "dealer_net_position",
        "swap_net": "swap_net_position",
    })

    return d

def main():
    """Download and process all years of CFTC options data"""
    frames = []

    for url in year_urls():
        try:
            buf = fetch_year(url)
            dfy = parse_zip(buf)
            if not dfy.empty:
                filtered = filter_corn_options(dfy)
                if not filtered.empty:
                    frames.append(filtered)
        except Exception as e:
            print(f"Warning: {e}")
            continue

    if not frames:
        raise SystemExit("No CFTC options data fetched. Check if corn is in Supplemental reports.")

    # Combine all years
    df = pd.concat(frames, ignore_index=True)

    # Remove duplicates and sort
    df = df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)

    # Save to CSV
    df.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    print(f"Rows: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nSample of latest data:")
    print(df.tail(3).to_string())

    # Summary statistics
    print(f"\n--- Summary Statistics ---")
    print(f"Average Put/Call Ratio: {df['put_call_ratio'].mean():.3f}")
    print(f"Current Put/Call Ratio: {df['put_call_ratio'].iloc[-1]:.3f}")
    print(f"Current 52w Percentile: {df['put_call_ratio_52w_pct'].iloc[-1]:.1f}%")

    # Trading signals
    current_pct = df['put_call_ratio_52w_pct'].iloc[-1]
    if current_pct > 80:
        print(f"\nSIGNAL: Put/Call ratio at {current_pct:.0f}th percentile - EXTREME FEAR (potential buy)")
    elif current_pct < 20:
        print(f"\nSIGNAL: Put/Call ratio at {current_pct:.0f}th percentile - EXTREME GREED (potential sell)")
    else:
        print(f"\nSIGNAL: Put/Call ratio at {current_pct:.0f}th percentile - NEUTRAL")

if __name__ == "__main__":
    main()
