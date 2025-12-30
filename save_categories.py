#!/usr/bin/env python3
"""
Save current stock categories to previous_categories.json
This should run BEFORE recalculate_rs.py in the GitHub Action
"""

import pandas as pd
import json
from pathlib import Path

def save_previous_categories():
    """Read current RS analysis and save category mapping"""
    
    csv_path = Path("saudiexchange_rs_analysis.csv")
    json_path = Path("previous_categories.json")
    
    if not csv_path.exists():
        print("[warn] saudiexchange_rs_analysis.csv not found, skipping category save")
        return
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"[info] Read {len(df)} rows from {csv_path}")
        
        # Create category mapping
        categories = {}
        
        for idx, row in df.iterrows():
            try:
                # Handle RS Validation
                rs_val = row.get('RS', 0)
                if pd.isna(rs_val) or str(rs_val).strip() == '':
                    continue
                rs = float(rs_val)
                
                # Handle Symbol Validation
                val = row.get('Symbol', '')
                if pd.isna(val) or str(val).strip().lower() in ['nan', '']:
                    continue
                
                # Clean Symbol
                try:
                    symbol = str(int(float(val)))
                except:
                    symbol = str(val).strip()
                
                # Determine Category
                if rs >= 90: category = 'STRONG'
                elif rs >= 80: category = 'IMPROVE'
                elif rs >= 70: category = 'NEUTRAL'
                else: category = 'WEAK'
                
                categories[symbol] = category
                
            except Exception as e:
                print(f"[warn] Failed to process row {idx}: {e}")
                continue
        
        if not categories:
            print("[error] No categories extracted! Checking first few rows of CSV:")
            print(df.head())
        
        # Save to JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        
        print(f"[success] Saved {len(categories)} stock categories to {json_path}")
        
    except Exception as e:
        print(f"[error] Failed to save categories: {e}")

if __name__ == "__main__":
    save_previous_categories()
