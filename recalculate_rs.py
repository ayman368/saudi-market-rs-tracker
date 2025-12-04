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
                "period": r.get("period", ""),
                "Change %": change_pct
            })
    
    if not data:
        print("[warn] no data to analyze")
        return

    df = pd.DataFrame(data)
    
    # Pivot: Company as index, period as columns, values are Change %
    df_pivot = df.pivot(index="Company", columns="period", values="Change %")
    
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
            # Calculate rank, round, clip, and convert to nullable integer (Int64) to remove decimals
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
    
    # Select and reorder columns for output
    output_cols = [col for col, _ in rs_cols] + [final_rs_col]
    
    # Save as Standard CSV
    df_pivot[output_cols].to_csv(output_path, encoding="utf-8-sig")
    print(f"[analysis] saved RS analysis to {output_path}")




if __name__ == "__main__":
    calculate_rs_metrics_from_csv("saudiexchange_results.csv", "saudiexchange_rs_analysis.csv")
