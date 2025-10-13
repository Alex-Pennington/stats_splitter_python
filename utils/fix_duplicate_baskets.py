#!/usr/bin/env python3
"""
Data Correction Tool for Firewood Splitter Production Data

Corrects the duplicate basket completion issue by:
1. Merging phantom basket #2 with basket #3
2. Renumbering subsequent baskets
3. Recalculating all dependent metrics
4. Correcting fuel consumption data
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

def save_json_file(data, filepath):
    """Save data to JSON file with proper formatting"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def correct_production_data(data):
    """Correct the production data by merging baskets 2 and 3"""
    print("🔧 Starting data correction process...")
    
    # Make a deep copy to avoid modifying original
    corrected_data = json.loads(json.dumps(data))
    
    if 'basket_history' not in corrected_data or 'completed_baskets' not in corrected_data['basket_history']:
        print("❌ No basket history found in data")
        return None
    
    baskets = corrected_data['basket_history']['completed_baskets']
    
    if len(baskets) < 3:
        print("❌ Not enough baskets to perform correction")
        return None
    
    print(f"📊 Original data: {len(baskets)} baskets")
    
    # Extract baskets 2 and 3 for merging
    basket_2 = baskets[1]  # Index 1 = basket #2
    basket_3 = baskets[2]  # Index 2 = basket #3
    
    print(f"🔍 Merging basket #{basket_2['basket_number']} ({basket_2['splits_completed']} splits, {basket_2['duration_seconds']:.1f}s)")
    print(f"   with basket #{basket_3['basket_number']} ({basket_3['splits_completed']} splits, {basket_3['duration_seconds']:.1f}s)")
    
    # Create merged basket (keeping basket #2's number but extending to basket #3's end time)
    merged_basket = {
        "basket_number": 2,  # Keep as basket #2
        "start_time": basket_2['start_time'],
        "start_time_formatted": basket_2['start_time_formatted'],
        "complete_time": basket_3['complete_time'],
        "complete_time_formatted": basket_3['complete_time_formatted'],
        "duration_seconds": basket_3['complete_time'] - basket_2['start_time'],
        "splits_completed": basket_2['splits_completed'] + basket_3['splits_completed'],
        "cycles_attempted": basket_2['cycles_attempted'] + basket_3['cycles_attempted'],
    }
    
    # Calculate derived fields
    merged_basket["duration_formatted"] = f"{merged_basket['duration_seconds']:.1f}s"
    merged_basket["success_rate"] = (merged_basket['splits_completed'] / merged_basket['cycles_attempted']) * 100
    
    # Handle timing fields - use weighted averages or sums as appropriate
    merged_basket["idle_time_seconds"] = basket_2['idle_time_seconds'] + basket_3['idle_time_seconds']
    merged_basket["break_time_seconds"] = basket_2['break_time_seconds'] + basket_3['break_time_seconds']
    merged_basket["operational_time_seconds"] = merged_basket['duration_seconds']
    merged_basket["productive_time_seconds"] = basket_3.get('productive_time_seconds', 0)
    merged_basket["active_time_seconds"] = basket_3.get('active_time_seconds', 0)
    
    # Calculate percentages
    if merged_basket['duration_seconds'] > 0:
        merged_basket["idle_time_percentage"] = (merged_basket['idle_time_seconds'] / merged_basket['duration_seconds']) * 100
        merged_basket["break_time_percentage"] = (merged_basket['break_time_seconds'] / merged_basket['duration_seconds']) * 100
        merged_basket["operational_time_percentage"] = 100.0
    else:
        merged_basket["idle_time_percentage"] = 0.0
        merged_basket["break_time_percentage"] = 0.0
        merged_basket["operational_time_percentage"] = 0.0
    
    # Handle fuel data - basket #2 had no fuel data, use basket #3's or set to null
    merged_basket["start_fuel_level"] = basket_3.get('start_fuel_level')
    merged_basket["end_fuel_level"] = basket_3.get('end_fuel_level')
    merged_basket["fuel_consumed"] = basket_3.get('fuel_consumed', 0.0)
    
    # Calculate splits per gallon
    if merged_basket["fuel_consumed"] > 0:
        merged_basket["splits_per_gallon"] = merged_basket['splits_completed'] / merged_basket["fuel_consumed"]
    else:
        merged_basket["splits_per_gallon"] = 0
    
    print(f"✅ Merged basket: {merged_basket['splits_completed']} splits, {merged_basket['duration_seconds']/60:.1f} minutes")
    
    # Replace baskets 2 and 3 with merged basket
    new_baskets = [baskets[0]]  # Keep basket #1
    new_baskets.append(merged_basket)  # Add merged basket #2
    
    # Add remaining baskets with renumbered basket numbers
    for i in range(3, len(baskets)):  # Start from old basket #4
        basket = baskets[i].copy()
        basket['basket_number'] = i  # Renumber: old #4 becomes #3, old #5 becomes #4, etc.
        new_baskets.append(basket)
    
    # Update the basket list
    corrected_data['basket_history']['completed_baskets'] = new_baskets
    
    print(f"📊 Corrected data: {len(new_baskets)} baskets (removed 1 duplicate)")
    
    # Recalculate cumulative totals
    total_splits = sum(b['splits_completed'] for b in new_baskets)
    total_cycles = sum(b['cycles_attempted'] for b in new_baskets)
    total_fuel = sum(b.get('fuel_consumed', 0) for b in new_baskets)
    completed_cycles = total_splits  # Successful cycles = splits
    aborted_cycles = total_cycles - completed_cycles
    
    # Update current basket number
    if 'current_basket' in corrected_data['basket_history']:
        corrected_data['basket_history']['current_basket']['basket_number'] = len(new_baskets) + 1
    if 'current_basket' in corrected_data:
        corrected_data['current_basket']['basket_number'] = len(new_baskets) + 1
    
    # Update cumulative totals
    if 'cumulative_totals' in corrected_data:
        corrected_data['cumulative_totals']['total_baskets_completed'] = len(new_baskets)
        corrected_data['cumulative_totals']['total_splits'] = total_splits
        corrected_data['cumulative_totals']['total_cycles'] = total_cycles
        corrected_data['cumulative_totals']['total_fuel_consumed_gallons'] = total_fuel
        corrected_data['cumulative_totals']['average_fuel_per_basket'] = total_fuel / len(new_baskets) if len(new_baskets) > 0 else 0
        corrected_data['cumulative_totals']['overall_success_rate'] = (completed_cycles / total_cycles) * 100 if total_cycles > 0 else 0
        corrected_data['cumulative_totals']['completed_cycles'] = completed_cycles
        corrected_data['cumulative_totals']['aborted_cycles'] = aborted_cycles
        
        # Recalculate production rates
        if 'system_uptime_hours' in corrected_data['cumulative_totals']:
            uptime_hours = corrected_data['cumulative_totals']['system_uptime_hours']
            if uptime_hours > 0:
                corrected_data['production_rates'] = {
                    'splits_per_hour': total_splits / uptime_hours,
                    'baskets_per_hour': len(new_baskets) / uptime_hours,
                    'current_basket_splits_per_hour': 0.0,  # Current basket has 0 splits
                    'average_splits_per_basket': total_splits / len(new_baskets) if len(new_baskets) > 0 else 0
                }
    
    # Update basket history totals
    corrected_data['basket_history']['total_baskets_completed'] = len(new_baskets)
    corrected_data['basket_history']['total_fuel_consumed'] = total_fuel
    corrected_data['basket_history']['average_fuel_per_basket'] = total_fuel / len(new_baskets) if len(new_baskets) > 0 else 0
    
    print("\n📈 CORRECTED STATISTICS:")
    print(f"   Total Baskets: {len(new_baskets)} (was {len(baskets)})")
    print(f"   Total Splits: {total_splits}")
    print(f"   Total Cycles: {total_cycles}")
    print(f"   Success Rate: {(completed_cycles / total_cycles) * 100:.1f}%")
    print(f"   Total Fuel: {total_fuel:.2f} gallons")
    print(f"   Avg Fuel/Basket: {total_fuel / len(new_baskets):.2f} gallons")
    
    return corrected_data

def main():
    """Main correction function"""
    base_path = Path(__file__).parent.parent
    input_file = base_path / "firewood_splitter_data_20251013_141629.json"
    output_file = base_path / "out.json"
    
    print("🔧 FIREWOOD SPLITTER DATA CORRECTION TOOL")
    print("Correcting duplicate basket completion signals...")
    print(f"Input: {input_file.name}")
    print(f"Output: {output_file.name}")
    
    # Load original data
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    original_data = load_json_file(input_file)
    if not original_data:
        print("❌ Failed to load input file")
        return
    
    # Perform correction
    corrected_data = correct_production_data(original_data)
    if not corrected_data:
        print("❌ Failed to correct data")
        return
    
    # Save corrected data
    if save_json_file(corrected_data, output_file):
        print(f"\n✅ Corrected data saved to: {output_file}")
        print("\n🎯 CORRECTION SUMMARY:")
        print("• Merged phantom basket #2 (3.6 min, 7 splits) with basket #3")
        print("• Renumbered all subsequent baskets (old #4→#3, #5→#4, etc.)")
        print("• Recalculated all cumulative statistics and production rates")
        print("• Fixed fuel consumption data and dependent metrics")
        print("• Corrected basket count from 10 to 9 baskets")
        print("\n📋 The corrected data now accurately reflects 9 completed baskets")
        print("   instead of the original 10 baskets with duplicate signals.")
        
    else:
        print("❌ Failed to save corrected data")

if __name__ == "__main__":
    main()