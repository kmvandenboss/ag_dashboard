#!/usr/bin/env python3

import io
import zipfile
import requests
import pandas as pd
from datetime import datetime

# CFTC Disaggregated Futures Only historical, zipped weekly CSVs combined per-year
# Docs: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
# We'll download the single "deacot_fut_xxxx.zip" per year (2006 -> current) and filter for SOYBEANS (CFTC market code 5)
# Note: Market and code names can change; we will match by "Market_and_Exchange_Names" containing "SOYBEAN" and "CBT" or "CBOT".

START_YEAR = 2006
OUT = "data/cot_soybean.csv"

def year_urls(start=START_YEAR):
    base = "https://www.cftc.gov/files/dea/history"
    current_year = datetime.now().year

    # For 2006-2016, use the consolidated historical file
    if start <= 2016:
        yield f"{base}/fut_disagg_txt_hist_2006_2016.zip"
        start = 2017  # Continue with individual years after 2016

    # Individual year files from 2017 onwards
    for y in range(start, current_year + 1):
        yield f"{base}/fut_disagg_txt_{y}.zip"

def fetch_year(url):
    print("Fetching", url)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return io.BytesIO(r.content)

def parse_zip(buf):
    with zipfile.ZipFile(buf) as z:
        # Each zip may contain one or more text files
        names = z.namelist()
        if not names:
            return pd.DataFrame()
        # Find the first .txt file (new format uses .txt instead of .csv)
        txt_file = next((n for n in names if n.endswith('.txt')), names[0])
        with z.open(txt_file) as f:
            df = pd.read_csv(f, low_memory=False)
    return df

def filter_soybean(df):
    # Standardize column names (some files differ slightly in case or spacing)
    df.columns = [c.strip() for c in df.columns]

    # Filter for SOYBEAN futures
    mask = df["Market_and_Exchange_Names"].str.contains("SOYBEAN", case=False, na=False) & \
           df["Market_and_Exchange_Names"].str.contains("CBT|CBOT|CHICAGO", case=False, na=False)
    d = df.loc[mask].copy()

    if len(d) == 0:
        print("Warning: No SOYBEAN records found in this file")
        return pd.DataFrame()

    # Normalize date
    d["date"] = pd.to_datetime(d["Report_Date_as_YYYY-MM-DD"])

    # Map actual column names to standardized names
    # CFTC uses format like: Open_Interest_All, M_Money_Positions_Long_All, etc.
    column_mapping = {
        "Open_Interest_All": "Open_Interest_(All)",
        "Prod_Merc_Positions_Long_All": "Producer_Merchant_Processor_User_Long_(All)",
        "Prod_Merc_Positions_Short_All": "Producer_Merchant_Processor_User_Short_(All)",
        "Swap_Positions_Long_All": "Swap_Dealer_Long_(All)",
        "Swap__Positions_Short_All": "Swap_Dealer_Short_(All)",  # Note: double underscore in CFTC data
        "M_Money_Positions_Long_All": "Money_Manager_Long_(All)",
        "M_Money_Positions_Short_All": "Money_Manager_Short_(All)",
        "Other_Rept_Positions_Long_All": "Other_Reportables_Long_(All)",
        "Other_Rept_Positions_Short_All": "Other_Reportables_Short_(All)",
        "NonRept_Positions_Long_All": "Nonreportable_Positions_Long_(All)",
        "NonRept_Positions_Short_All": "Nonreportable_Positions_Short_(All)",
    }

    # Rename columns
    d = d.rename(columns=column_mapping)

    # Pick relevant columns
    keep = [
        "date",
        "Open_Interest_(All)",
        "Producer_Merchant_Processor_User_Long_(All)",
        "Producer_Merchant_Processor_User_Short_(All)",
        "Swap_Dealer_Long_(All)",
        "Swap_Dealer_Short_(All)",
        "Money_Manager_Long_(All)",
        "Money_Manager_Short_(All)",
        "Other_Reportables_Long_(All)",
        "Other_Reportables_Short_(All)",
        "Nonreportable_Positions_Long_(All)",
        "Nonreportable_Positions_Short_(All)",
    ]

    # Some historical files might miss a column or two; fill gracefully
    for c in keep:
        if c not in d.columns:
            d[c] = pd.NA

    d = d[keep].sort_values("date").reset_index(drop=True)

    # Convert to numeric (handle any string values or commas)
    numeric_cols = [
        "Open_Interest_(All)",
        "Producer_Merchant_Processor_User_Long_(All)",
        "Producer_Merchant_Processor_User_Short_(All)",
        "Swap_Dealer_Long_(All)",
        "Swap_Dealer_Short_(All)",
        "Money_Manager_Long_(All)",
        "Money_Manager_Short_(All)",
        "Other_Reportables_Long_(All)",
        "Other_Reportables_Short_(All)",
        "Nonreportable_Positions_Long_(All)",
        "Nonreportable_Positions_Short_(All)",
    ]
    for col in numeric_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors='coerce')

    # Derive nets
    d["mm_net"] = d["Money_Manager_Long_(All)"] - d["Money_Manager_Short_(All)"]
    d["prod_net"] = d["Producer_Merchant_Processor_User_Long_(All)"] - d["Producer_Merchant_Processor_User_Short_(All)"]
    d["swap_net"] = d["Swap_Dealer_Long_(All)"] - d["Swap_Dealer_Short_(All)"]
    d["other_net"] = d["Other_Reportables_Long_(All)"] - d["Other_Reportables_Short_(All)"]
    d["nonrep_net"] = d["Nonreportable_Positions_Long_(All)"] - d["Nonreportable_Positions_Short_(All)"]

    # COT Index (0-100) for Money Managers using rolling 52w range
    d["mm_net_52w_min"] = d["mm_net"].rolling(52, min_periods=1).min()
    d["mm_net_52w_max"] = d["mm_net"].rolling(52, min_periods=1).max()
    d["mm_net_index"] = (d["mm_net"] - d["mm_net_52w_min"]) / (d["mm_net_52w_max"] - d["mm_net_52w_min"]).replace(0, pd.NA) * 100

    # Clean
    d = d.drop(columns=["mm_net_52w_min", "mm_net_52w_max"])

    print(f"  Extracted {len(d)} SOYBEAN records")
    return d

def main():
    frames = []
    for url in year_urls():
        try:
            buf = fetch_year(url)
            dfy = parse_zip(buf)
            if not dfy.empty:
                frames.append(dfy)
        except Exception as e:
            print("Warning:", e)
    if not frames:
        raise SystemExit("No COT data fetched.")
    df = pd.concat(frames, ignore_index=True)
    dsoy = filter_soybean(df)
    dsoy.to_csv(OUT, index=False)
    print("Wrote", OUT, "rows:", len(dsoy))

if __name__ == "__main__":
    main()
