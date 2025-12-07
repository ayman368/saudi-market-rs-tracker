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
    try:
        symbols_path = "company_symbols.csv"
        # Read simple CSV with header: #,Company,الرمز على تريدنج فيو
        # encoding might be utf-8-sig or utf-8
        try:
            df_sym = pd.read_csv(symbols_path)
        except Exception:
            # try different encoding if default fails
            df_sym = pd.read_csv(symbols_path, encoding='utf-8-sig')
            
        # Rename columns to be English friendly
        # Assuming column order: [Code, CompanyString, TradingView]
        # Or by name if possible. Let's try by known names from file view.
        # File header: #,Company,الرمز على تريدنج فيو
        # We want to map 'Company' -> 'Company' to merge.
        # And keep '#' as 'Code' and 'الرمز على تريدنج فيو' as 'TradingView'
        
        # Normalize columns
        df_sym.columns = [c.strip() for c in df_sym.columns]
        
        # Use index-based renaming to avoid encoding issues
        # Expecting at least 3 columns: Code (#), Company, TradingView
        if len(df_sym.columns) >= 3:
            df_sym.columns.values[0] = 'Code'
            df_sym.columns.values[1] = 'Company' 
            df_sym.columns.values[2] = 'TradingView'
            
            # Drop duplicates if any in symbols file
            df_sym = df_sym.drop_duplicates(subset=['Company'])
            
            # Merge
            df_pivot = pd.merge(df_pivot, df_sym[['Company', 'Code', 'TradingView']], on='Company', how='left')
            
            print("[analysis] Merged with company_symbols.csv")
        else:
            print(f"[warn] Unexpected columns in symbols file: {df_sym.columns}")

    except FileNotFoundError:
        print("[warn] company_symbols.csv not found, skipping merge")
    except Exception as e:
        print(f"[warn] Failed to merge symbols: {e}")

    # Remove the old 'Symbol' column extracted from scraper if we have a better one, 
    # OR prefer the one from CSV. 
    # The scraper extract might be empty or partial. The CSV is the master.
    # If merged successfully, we have 'Code' and 'TradingView'.
    # We can keep 'Code' as the main 'Code'.
    
    # Select and reorder columns for output
    # Desired: Company, Code, TradingView, RS columns..., RS
    
    # Check which columns we actually have
    final_cols = ["Company"]
    if "Code" in df_pivot.columns:
        final_cols.append("Code")
    if "TradingView" in df_pivot.columns:
        final_cols.append("TradingView")
    # If we extracted 'Symbol' from scraper and it's not the same as SymbolCode, maybe keep it?
    # User asked for columns from the excel. Let's prioritize those.
    # If SymbolCode is present, use it.
    
    # Add RS columns
    final_cols.extend([col for col, _ in rs_cols])
    final_cols.append(final_rs_col)
    
    # Save as Standard CSV
    df_pivot[final_cols].to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[analysis] saved RS analysis to {output_path}")

if __name__ == "__main__":
    calculate_rs_metrics_from_csv("saudiexchange_results.csv", "saudiexchange_rs_analysis.csv")
