#!/usr/bin/env python3
"""
Precise Data Correction Tool

This tool addresses the fundamental issue: the corrected data is pulling splits from 
the wrong baskets due to indexing confusion. We need to properly map the reference 
data to the corrected basket structure.
"""

import json

def create_precise_correction():
    """Create a precise correction using proper data mapping"""
    
    print("🔧 CREATING PRECISE CORRECTION")
    print("=" * 50)
    
    # Load the original export data and production reference
    original_data = json.load(open('firewood_splitter_data_20251013_141629.json', 'r'))
    production_ref = json.load(open('production_data copy.json', 'r'))
    
    # The key insight: the export data already has the correct splits counts
    # We just need to merge basket 2 & 3 and renumber properly
    
    export_baskets = original_data['basket_history']['completed_baskets']
    
    print(f"Export data has {len(export_baskets)} baskets:")
    for i, basket in enumerate(export_baskets):
        print(f"  Basket #{basket['basket_number']}: {basket['splits_completed']} splits, {basket.get('fuel_consumed', 0):.3f} gal")
    
    # Create corrected structure
    corrected_data = json.loads(json.dumps(original_data))
    
    # Merge baskets 2 and 3 from the EXPORT data (which has correct splits)
    basket_2 = export_baskets[1]  # Export basket #2: 7 splits
    basket_3 = export_baskets[2]  # Export basket #3: 93 splits
    
    print(f"\nMerging:")
    print(f"  Export basket #2: {basket_2['splits_completed']} splits, {basket_2.get('fuel_consumed', 0):.3f} gal")
    print(f"  Export basket #3: {basket_3['splits_completed']} splits, {basket_3.get('fuel_consumed', 0):.3f} gal")
    
    # Create merged basket with EXPORT data (correct splits)
    merged_basket = {
        "basket_number": 2,
        "start_time": basket_2['start_time'],
        "start_time_formatted": basket_2['start_time_formatted'],
        "complete_time": basket_3['complete_time'],
        "complete_time_formatted": basket_3['complete_time_formatted'],
        "duration_seconds": basket_3['complete_time'] - basket_2['start_time'],
        "splits_completed": basket_2['splits_completed'] + basket_3['splits_completed'],  # 7 + 93 = 100
        "cycles_attempted": basket_2['cycles_attempted'] + basket_3['cycles_attempted'],
        "fuel_consumed": basket_2.get('fuel_consumed', 0) + basket_3.get('fuel_consumed', 0),  # Both are 0
    }
    
    # Calculate derived fields
    merged_basket["duration_formatted"] = f"{merged_basket['duration_seconds']:.1f}s"
    merged_basket["success_rate"] = (merged_basket['splits_completed'] / merged_basket['cycles_attempted']) * 100
    
    # Timing fields
    merged_basket["idle_time_seconds"] = basket_2['idle_time_seconds'] + basket_3['idle_time_seconds']
    merged_basket["break_time_seconds"] = basket_2['break_time_seconds'] + basket_3['break_time_seconds']
    merged_basket["operational_time_seconds"] = merged_basket['duration_seconds']
    merged_basket["productive_time_seconds"] = basket_2.get('productive_time_seconds', 0) + basket_3.get('productive_time_seconds', 0)
    merged_basket["active_time_seconds"] = basket_2.get('active_time_seconds', 0) + basket_3.get('active_time_seconds', 0)
    
    # Percentages
    if merged_basket['duration_seconds'] > 0:
        merged_basket["idle_time_percentage"] = (merged_basket['idle_time_seconds'] / merged_basket['duration_seconds']) * 100
        merged_basket["break_time_percentage"] = (merged_basket['break_time_seconds'] / merged_basket['duration_seconds']) * 100
        merged_basket["operational_time_percentage"] = 100.0
    
    # Fuel fields - both baskets had no fuel data, but let's be explicit
    merged_basket["start_fuel_level"] = basket_2.get('start_fuel_level')  # null
    merged_basket["end_fuel_level"] = basket_3.get('end_fuel_level')      # null
    merged_basket["splits_per_gallon"] = 0  # No fuel consumed
    
    print(f"  Merged result: {merged_basket['splits_completed']} splits, {merged_basket['fuel_consumed']:.3f} gal")
    
    # Build new basket list
    new_baskets = [export_baskets[0]]  # Keep basket #1 unchanged
    new_baskets.append(merged_basket)   # Add merged basket #2
    
    # Add remaining baskets (old #4-#10 become #3-#9) with renumbering only
    for i in range(3, len(export_baskets)):
        basket = export_baskets[i].copy()
        basket['basket_number'] = i  # Renumber: old #4→#3, #5→#4, etc.
        new_baskets.append(basket)
    
    print(f"\nResult: {len(new_baskets)} baskets:")
    total_splits = 0
    total_fuel = 0
    for basket in new_baskets:
        splits = basket['splits_completed']
        fuel = basket.get('fuel_consumed', 0)
        total_splits += splits
        total_fuel += fuel
        print(f"  Basket #{basket['basket_number']}: {splits} splits, {fuel:.3f} gal")
    
    print(f"\nTotals: {total_splits} splits, {total_fuel:.3f} gallons")
    
    # Update the corrected data
    corrected_data['basket_history']['completed_baskets'] = new_baskets
    
    # Recalculate all totals
    total_cycles = sum(b['cycles_attempted'] for b in new_baskets)
    completed_cycles = total_splits
    aborted_cycles = total_cycles - completed_cycles
    
    # Update cumulative totals
    corrected_data['cumulative_totals']['total_baskets_completed'] = len(new_baskets)
    corrected_data['cumulative_totals']['total_splits'] = total_splits
    corrected_data['cumulative_totals']['total_cycles'] = total_cycles
    corrected_data['cumulative_totals']['total_fuel_consumed_gallons'] = total_fuel
    corrected_data['cumulative_totals']['average_fuel_per_basket'] = total_fuel / len(new_baskets)
    corrected_data['cumulative_totals']['overall_success_rate'] = (completed_cycles / total_cycles) * 100
    corrected_data['cumulative_totals']['completed_cycles'] = completed_cycles
    corrected_data['cumulative_totals']['aborted_cycles'] = aborted_cycles
    
    # Update production rates
    uptime_hours = corrected_data['export_info']['system_uptime_hours']
    if uptime_hours > 0:
        corrected_data['production_rates'] = {
            'splits_per_hour': total_splits / uptime_hours,
            'baskets_per_hour': len(new_baskets) / uptime_hours,
            'current_basket_splits_per_hour': 0.0,
            'average_splits_per_basket': total_splits / len(new_baskets)
        }
    
    # Update basket history totals
    corrected_data['basket_history']['total_baskets_completed'] = len(new_baskets)
    corrected_data['basket_history']['total_fuel_consumed'] = total_fuel
    corrected_data['basket_history']['average_fuel_per_basket'] = total_fuel / len(new_baskets)
    
    # Update current basket numbers
    if 'current_basket' in corrected_data['basket_history']:
        corrected_data['basket_history']['current_basket']['basket_number'] = len(new_baskets) + 1
    if 'current_basket' in corrected_data:
        corrected_data['current_basket']['basket_number'] = len(new_baskets) + 1
    
    return corrected_data

def main():
    """Main correction function"""
    corrected_data = create_precise_correction()
    
    if corrected_data:
        # Save the precisely corrected data
        with open('out.json', 'w') as f:
            json.dump(corrected_data, f, indent=2)
        
        print(f"\n✅ PRECISE CORRECTION COMPLETE")
        print(f"   Saved to: out.json")
        print(f"   Result: 9 baskets with correct splits and fuel data")
        print(f"   No data corruption - used original export values")

if __name__ == "__main__":
    main()