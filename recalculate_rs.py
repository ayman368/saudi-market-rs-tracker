import json
import csv
import sys
import pandas as pd
import numpy as np

def calculate_rs_metrics_from_csv(input_csv: str, output_path: str) -> None:
    print(f"[init] reading data from {input_csv}")
    
    # Read the CSV manually to handle the structure
    data = []
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Clean Change %: remove '%' and convert to float
            try:
                change_pct_str = r.get("Change %", "").replace("%", "").strip()
                change_pct = float(change_pct_str) if change_pct_str else None
            except ValueError:
                change_pct = None
                
            data.append({
                "Company": r.get("Company", ""),
                "Symbol": r.get("Symbol", ""),
                "period": r.get("period", ""),
                "Change %": change_pct
            })
    
    if not data:
        print("[warn] no data to analyze")
        return

    df = pd.DataFrame(data)
    
    # Normalize Company names to uppercase to handle inconsistencies (e.g. WAFA INSURANCE vs WAFA Insurance)
    df["Company"] = df["Company"].astype(str).str.strip().str.upper()

    # Pivot: Company and Symbol as index
    # We use a list of index columns to preserve the Symbol
    df_pivot = df.pivot(index=["Company", "Symbol"], columns="period", values="Change %")
    
    # Define periods and weights
    period_map = {
        "1 Year": 0.2,
        "9 Months": 0.2,
        "6 Months": 0.2,
        "3 Months": 0.4
    }
    
    # Calculate RS for each period
    rs_cols = []
    for p, weight in period_map.items():
        if p in df_pivot.columns:
            col_name = f"RS_{p.replace(' ', '')}"
            # Calculate rank, round, clip, and convert to nullable integer (Int64)
            df_pivot[col_name] = (df_pivot[p].rank(pct=True) * 100).round(0).clip(upper=99).astype('Int64')
            rs_cols.append((col_name, weight))
        else:
            print(f"[warn] period '{p}' not found in data")

    # Calculate Final RS
    final_rs_col = "RS"
    weighted_sum = 0
    for col, weight in rs_cols:
        weighted_sum += df_pivot[col].fillna(0) * weight
    
    df_pivot[final_rs_col] = np.ceil(weighted_sum).astype('Int64')
    
    # Reset index to make Company and Symbol regular columns again
    df_pivot.reset_index(inplace=True)

    # --- MERGE WITH USER PROVIDED SYMBOLS ---
    # First, drop the 'Symbol' column from pivot if it exists (from scraper)
    # We'll use the Symbol from company_symbols.csv instead
    if 'Symbol' in df_pivot.columns:
        df_pivot = df_pivot.drop(columns=['Symbol'])
    
    try:
        symbols_path = "company_symbols.csv"
        # Read simple CSV with header: #,Company,الرمز على تريدنج فيو
        # encoding might be utf-8-sig or utf-8
        try:
            df_sym = pd.read_csv(symbols_path)
        except Exception:
            # try different encoding if default fails
            df_sym = pd.read_csv(symbols_path, encoding='utf-8-sig')
            
        # Normalize columns
        df_sym.columns = [c.strip() for c in df_sym.columns]
        
        # Use index-based renaming to avoid encoding issues
        # Expecting at least 3 columns: Code (#), Company, TradingView
        if len(df_sym.columns) >= 3:
            df_sym.columns.values[0] = 'Symbol'
            df_sym.columns.values[1] = 'Company' 
            df_sym.columns.values[2] = 'TradingView'
            
            # Normalize Company in symbols to uppercase
            if 'Company' in df_sym.columns:
                 df_sym['Company'] = df_sym['Company'].astype(str).str.strip().str.upper()

            # Drop duplicates if any in symbols file
            df_sym = df_sym.drop_duplicates(subset=['Company'])
            
            # Merge
            df_pivot = pd.merge(df_pivot, df_sym[['Company', 'Symbol', 'TradingView']], on='Company', how='left')
            
            print("[analysis] Merged with company_symbols.csv")
        else:
            print(f"[warn] Unexpected columns in symbols file: {df_sym.columns}")

    except FileNotFoundError:
        print("[warn] company_symbols.csv not found, skipping merge")
    except Exception as e:
        print(f"[warn] Failed to merge symbols: {e}")

    # Select and reorder columns for output
    # Desired: Company, Symbol, TradingView, RS columns..., RS
    
    # Check which columns we actually have
    final_cols = ["Company"]
    if "Symbol" in df_pivot.columns:
        final_cols.append("Symbol")
    if "TradingView" in df_pivot.columns:
        final_cols.append("TradingView")
    
    # Add RS columns
    final_cols.extend([col for col, _ in rs_cols])
    final_cols.append(final_rs_col)
    
    # Save as Standard CSV
    df_pivot[final_cols].to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[analysis] saved RS analysis to {output_path}")
    
    # --- CALCULATE TRADINGVIEW THRESHOLDS ---
    # Calculate weighted performance for each stock (simulates TradingView's totalRsScore)
    print("[thresholds] calculating weighted performance scores for TradingView...")
    
    performance_scores = []
    
    for idx, row in df_pivot.iterrows():
        company = row['Company']
        
        # Get raw Change % for each period
        perfs = {}
        valid_count = 0
        for p in period_map.keys():
            if p in df_pivot.columns:
                val = row[p]
                if pd.notna(val):
                    perfs[p] = val
                    valid_count += 1
        
        # Skip if missing data
        if valid_count < len(period_map):
            continue
        
        # Calculate weighted performance (matching TradingView formula)
        # Using weights: 40% for 3M, 20% for 6M, 20% for 9M, 20% for 1Y
        weighted_perf = 0
        for p, weight in period_map.items():
            if p in perfs:
                # Convert percentage to ratio (e.g., 10% -> 1.10)
                weighted_perf += (1 + perfs[p]/100) * weight
        
        # Store the weighted performance and RS
        performance_scores.append({
            'Company': company,
            'WeightedPerformance': weighted_perf,
            'RS': row[final_rs_col]
        })
    
    df_perf = pd.DataFrame(performance_scores)
    
    if len(df_perf) == 0:
        print("[warn] no performance scores calculated")
        return
    
    # Calculate median as "market proxy" (like TASI average)
    median_perf = df_perf['WeightedPerformance'].median()
    
    # Calculate relative score: (stock_perf / median_perf) * 100
    # This matches TradingView's totalRsScore calculation
    df_perf['RelativeScore'] = (df_perf['WeightedPerformance'] / median_perf) * 100
    
    # Now calculate percentile thresholds based on RelativeScore
    # These are the raw score values that correspond to each percentile
    percentiles_from_score = {
        99: df_perf['RelativeScore'].quantile(0.99),  # Top 1%
        90: df_perf['RelativeScore'].quantile(0.90),  # Top 10%
        70: df_perf['RelativeScore'].quantile(0.70),  # Top 30%
        50: df_perf['RelativeScore'].quantile(0.50),  # Median
        30: df_perf['RelativeScore'].quantile(0.30),  # Bottom 70%
        10: df_perf['RelativeScore'].quantile(0.10),  # Bottom 90%
        1:  df_perf['RelativeScore'].quantile(0.01)   # Bottom 99%
    }
    
    # Save thresholds to JSON
    thresholds_path = output_path.replace('.csv', '_tv_thresholds.json')
    with open(thresholds_path, 'w', encoding='utf-8') as f:
        json.dump(percentiles_from_score, f, indent=2)
    print(f"[thresholds] saved to {thresholds_path}")
    
    # Save as readable text for TradingView
    thresholds_txt = output_path.replace('.csv', '_tv_thresholds.txt')
    with open(thresholds_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("TradingView RS Rating Thresholds for Saudi Market\n")
        f.write("=" * 60 + "\n\n")
        f.write("Copy these values to your TradingView indicator settings:\n")
        f.write("(Saudi Market Calibration section)\n\n")
        f.write(f"For 99 Rating (Top 1%):   {percentiles_from_score[99]:.2f}\n")
        f.write(f"For 90+ Rating (Top 10%): {percentiles_from_score[90]:.2f}\n")
        f.write(f"For 70+ Rating:           {percentiles_from_score[70]:.2f}\n")
        f.write(f"For 50+ Rating (Median):  {percentiles_from_score[50]:.2f}\n")
        f.write(f"For 30+ Rating:           {percentiles_from_score[30]:.2f}\n")
        f.write(f"For 10+ Rating:           {percentiles_from_score[10]:.2f}\n")
        f.write(f"For 1 Rating (Bottom):    {percentiles_from_score[1]:.2f}\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write("HOW TO USE:\n")
        f.write("1. Open TradingView\n")
        f.write("2. Add 'Saudi RS Rating' indicator to your chart\n")
        f.write("3. Open indicator settings\n")
        f.write("4. Go to 'Saudi Market Calibration' section\n")
        f.write("5. Copy the values above into the corresponding fields\n")
        f.write("6. Click OK\n")
        f.write("\nThese thresholds are updated daily by GitHub Actions.\n")
        f.write("Last update: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    print(f"[thresholds] saved readable version to {thresholds_txt}")
    
    # Also print to console for easy viewing
    print("\n" + "=" * 60)
    print("📊 TRADINGVIEW THRESHOLDS (Copy to TradingView settings):")
    print("=" * 60)
    print(f"For 99 Rating (Top 1%):   {percentiles_from_score[99]:.2f}")
    print(f"For 90+ Rating (Top 10%): {percentiles_from_score[90]:.2f}")
    print(f"For 70+ Rating:           {percentiles_from_score[70]:.2f}")
    print(f"For 50+ Rating (Median):  {percentiles_from_score[50]:.2f}")
    print(f"For 30+ Rating:           {percentiles_from_score[30]:.2f}")
    print(f"For 10+ Rating:           {percentiles_from_score[10]:.2f}")
    print(f"For 1 Rating (Bottom):    {percentiles_from_score[1]:.2f}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    calculate_rs_metrics_from_csv("saudiexchange_results.csv", "saudiexchange_rs_analysis.csv")
