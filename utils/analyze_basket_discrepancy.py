#!/usr/bin/env python3
"""
Basket Discrepancy Analysis Tool

Analyzes production data files to identify basket counting inconsistencies,
duplicate basket completion signals, and data integrity issues.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def load_json_file(filepath):
    """Load and parse JSON file with error handling"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def analyze_basket_data(data, filename):
    """Analyze basket data for inconsistencies"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {filename}")
    print(f"{'='*60}")
    
    # Extract key data
    if 'cumulative_totals' in data:
        reported_total = data['cumulative_totals'].get('total_baskets_completed', 0)
        print(f"📊 Reported Total Baskets: {reported_total}")
    else:
        reported_total = data.get('total_baskets', 0)
        print(f"📊 Reported Total Baskets: {reported_total}")
    
    # Count completed baskets in basket_history
    if 'basket_history' in data and 'completed_baskets' in data['basket_history']:
        completed_baskets = data['basket_history']['completed_baskets']
        actual_completed = len(completed_baskets)
        print(f"📋 Actual Completed Baskets in History: {actual_completed}")
        
        # Analyze each basket
        print(f"\n🔍 BASKET DETAILS:")
        print(f"{'#':<3} {'Start Time':<20} {'Complete Time':<20} {'Splits':<7} {'Duration (min)':<15} {'Gap (sec)':<10}")
        print("-" * 85)
        
        prev_complete_time = None
        total_splits_calculated = 0
        
        for i, basket in enumerate(completed_baskets):
            basket_num = basket.get('basket_number', i+1)
            start_time = basket.get('start_time', 0)
            complete_time = basket.get('complete_time', 0)
            splits = basket.get('splits_completed', 0)
            duration_sec = basket.get('duration_seconds', 0)
            duration_min = duration_sec / 60
            
            # Format times
            start_formatted = datetime.fromtimestamp(start_time).strftime('%H:%M:%S') if start_time else "N/A"
            complete_formatted = datetime.fromtimestamp(complete_time).strftime('%H:%M:%S') if complete_time else "N/A"
            
            # Calculate gap from previous basket
            gap = ""
            if prev_complete_time and start_time:
                gap_sec = start_time - prev_complete_time
                gap = f"{gap_sec:.1f}s"
            
            print(f"{basket_num:<3} {start_formatted:<20} {complete_formatted:<20} {splits:<7} {duration_min:<15.1f} {gap:<10}")
            
            total_splits_calculated += splits
            prev_complete_time = complete_time
        
        print(f"\n📈 CALCULATED TOTALS:")
        print(f"   Total Splits from Baskets: {total_splits_calculated}")
        
        # Check if there's a current basket
        if 'current_basket' in data['basket_history']:
            current = data['basket_history']['current_basket']
            current_splits = current.get('splits_completed', 0)
            current_basket_num = current.get('basket_number', 'Unknown')
            print(f"   Current Basket #{current_basket_num} Splits: {current_splits}")
            total_splits_calculated += current_splits
        elif 'current_basket' in data:
            current = data['current_basket']
            current_splits = current.get('splits_completed', 0)
            current_basket_num = current.get('basket_number', 'Unknown')
            print(f"   Current Basket #{current_basket_num} Splits: {current_splits}")
            total_splits_calculated += current_splits
        
        print(f"   TOTAL SPLITS (calculated): {total_splits_calculated}")
        
    elif 'completed_baskets' in data:
        # Handle old format
        completed_baskets = data['completed_baskets']
        actual_completed = len(completed_baskets)
        print(f"📋 Actual Completed Baskets in History: {actual_completed}")
        
        total_splits_calculated = sum(len(basket.get('cycles', [])) for basket in completed_baskets if 'cycles' in basket)
        print(f"📈 Total Splits from Cycle Count: {total_splits_calculated}")
    
    # Compare with reported totals
    if 'cumulative_totals' in data:
        reported_splits = data['cumulative_totals'].get('total_splits', 0)
        print(f"📊 Reported Total Splits: {reported_splits}")
        
        if total_splits_calculated != reported_splits:
            print(f"⚠️  SPLITS MISMATCH: Calculated ({total_splits_calculated}) != Reported ({reported_splits})")
            print(f"   Difference: {reported_splits - total_splits_calculated}")
    elif 'total_splits' in data:
        reported_splits = data.get('total_splits', 0)
        print(f"📊 Reported Total Splits: {reported_splits}")
        
        if total_splits_calculated != reported_splits:
            print(f"⚠️  SPLITS MISMATCH: Calculated ({total_splits_calculated}) != Reported ({reported_splits})")
    
    # Check for basket number inconsistencies
    if 'basket_history' in data and 'completed_baskets' in data['basket_history']:
        basket_numbers = [b.get('basket_number', 0) for b in data['basket_history']['completed_baskets']]
        expected_numbers = list(range(1, len(basket_numbers) + 1))
        
        if basket_numbers != expected_numbers:
            print(f"⚠️  BASKET NUMBERING ISSUE:")
            print(f"   Expected: {expected_numbers}")
            print(f"   Actual:   {basket_numbers}")
            
            # Check for duplicates
            duplicates = [num for num in set(basket_numbers) if basket_numbers.count(num) > 1]
            if duplicates:
                print(f"   🔴 DUPLICATE BASKET NUMBERS: {duplicates}")
            
            # Check for gaps
            missing = [num for num in expected_numbers if num not in basket_numbers]
            if missing:
                print(f"   🔴 MISSING BASKET NUMBERS: {missing}")
    
    # Analyze timing gaps for suspicious basket completion signals
    if 'basket_history' in data and 'completed_baskets' in data['basket_history']:
        print(f"\n⏰ TIMING ANALYSIS:")
        baskets = data['basket_history']['completed_baskets']
        
        for i in range(len(baskets) - 1):
            current = baskets[i]
            next_basket = baskets[i + 1]
            
            current_complete = current.get('complete_time', 0)
            next_start = next_basket.get('start_time', 0)
            
            if current_complete and next_start:
                gap = next_start - current_complete
                current_num = current.get('basket_number', i+1)
                next_num = next_basket.get('basket_number', i+2)
                
                if gap < 1.0:  # Less than 1 second gap
                    print(f"   🔴 SUSPICIOUS: Basket {current_num} → {next_num}, gap: {gap:.3f}s (possible duplicate signal)")
                elif gap > 300:  # More than 5 minute gap
                    gap_min = gap / 60
                    print(f"   ⚠️  LONG GAP: Basket {current_num} → {next_num}, gap: {gap_min:.1f} minutes")

def main():
    """Main analysis function"""
    base_path = Path(__file__).parent.parent
    
    # Files to analyze
    files_to_analyze = [
        base_path / "firewood_splitter_data_20251013_141629.json",
        base_path / "production_data copy.json",
        base_path / "production_data.json"
    ]
    
    print("🔍 BASKET DISCREPANCY ANALYSIS")
    print("Analyzing production data files for basket counting issues...")
    
    for filepath in files_to_analyze:
        if filepath.exists():
            data = load_json_file(filepath)
            if data:
                analyze_basket_data(data, filepath.name)
        else:
            print(f"\n⚠️  File not found: {filepath.name}")
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print("\nLook for:")
    print("🔴 SUSPICIOUS gaps < 1 second (possible duplicate signals)")
    print("⚠️  MISMATCHES between calculated and reported totals")
    print("🔴 DUPLICATE basket numbers")
    print("⚠️  LONG GAPS between baskets (operational issues)")

if __name__ == "__main__":
    main()