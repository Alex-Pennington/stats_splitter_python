#!/usr/bin/env python3
"""
Enhanced Data Correction Tool - Analyzing splits and fuel discrepancies

This script will:
1. Compare the corrected data against the production reference
2. Identify splits count mismatches
3. Fix fuel consumption mapping
4. Recalculate all dependent metrics properly
"""

import json
from datetime import datetime

def load_json_file(filepath):
    """Load and parse JSON file with error handling"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def analyze_data_discrepancies():
    """Analyze discrepancies between corrected data and production reference"""
    
    # Load both files
    corrected_data = load_json_file('out.json')
    production_ref = load_json_file('production_data copy.json')
    
    if not corrected_data or not production_ref:
        print("❌ Failed to load data files")
        return None
    
    print("🔍 ANALYZING DATA DISCREPANCIES")
    print("=" * 50)
    
    # Get basket data
    corrected_baskets = corrected_data['basket_history']['completed_baskets']
    ref_baskets = production_ref['completed_baskets']
    
    print(f"Corrected data: {len(corrected_baskets)} baskets")
    print(f"Reference data: {len(ref_baskets)} baskets")
    
    # Compare basket by basket
    print("\n📊 BASKET-BY-BASKET COMPARISON:")
    print("Basket | Corrected | Reference | Fuel(Corr) | Fuel(Ref) | Status")
    print("-" * 70)
    
    total_splits_corrected = 0
    total_splits_reference = 0
    fuel_issues = []
    splits_issues = []
    
    for i in range(min(len(corrected_baskets), len(ref_baskets))):
        corr_basket = corrected_baskets[i]
        ref_basket = ref_baskets[i]
        
        corr_splits = corr_basket['splits_completed']
        ref_splits = len([cycle for cycle in ref_basket['cycles'] if not cycle.get('aborted', False)])
        
        corr_fuel = corr_basket.get('fuel_consumed', 0)
        ref_fuel = ref_basket.get('fuel_consumed', 0)
        
        total_splits_corrected += corr_splits
        total_splits_reference += ref_splits
        
        status = "✓"
        if corr_splits != ref_splits:
            status = "❌ SPLITS"
            splits_issues.append((i+1, corr_splits, ref_splits))
        
        if abs(corr_fuel - ref_fuel) > 0.01:
            status += " ❌ FUEL"
            fuel_issues.append((i+1, corr_fuel, ref_fuel))
        
        print(f"  {i+1:2d}   |    {corr_splits:3d}    |    {ref_splits:3d}    |   {corr_fuel:.2f}   |   {ref_fuel:.2f}   | {status}")
    
    print("-" * 70)
    print(f"TOTALS |    {total_splits_corrected:3d}    |    {total_splits_reference:3d}    |")
    
    # Check the merged basket specifically (basket #2)
    if len(corrected_baskets) >= 2 and len(ref_baskets) >= 3:
        print(f"\n🔍 MERGED BASKET #2 ANALYSIS:")
        merged_basket = corrected_baskets[1]  # Basket #2 in corrected data
        orig_basket_2 = ref_baskets[1]        # Original basket #2 in reference
        orig_basket_3 = ref_baskets[2]        # Original basket #3 in reference
        
        # Count actual splits from cycles
        orig_2_splits = len([c for c in orig_basket_2['cycles'] if not c.get('aborted', False)])
        orig_3_splits = len([c for c in orig_basket_3['cycles'] if not c.get('aborted', False)])
        expected_merged_splits = orig_2_splits + orig_3_splits
        
        print(f"Original basket #2 splits: {orig_2_splits}")
        print(f"Original basket #3 splits: {orig_3_splits}")
        print(f"Expected merged splits: {expected_merged_splits}")
        print(f"Actual merged splits: {merged_basket['splits_completed']}")
        
        if merged_basket['splits_completed'] != expected_merged_splits:
            print(f"❌ MERGED BASKET SPLITS MISMATCH!")
        
        # Check fuel for merged basket
        orig_2_fuel = orig_basket_2.get('fuel_consumed', 0)
        orig_3_fuel = orig_basket_3.get('fuel_consumed', 0)
        expected_fuel = orig_2_fuel + orig_3_fuel
        actual_fuel = merged_basket.get('fuel_consumed', 0)
        
        print(f"Original basket #2 fuel: {orig_2_fuel}")
        print(f"Original basket #3 fuel: {orig_3_fuel}")
        print(f"Expected merged fuel: {expected_fuel}")
        print(f"Actual merged fuel: {actual_fuel}")
    
    return {
        'splits_issues': splits_issues,
        'fuel_issues': fuel_issues,
        'total_splits_corrected': total_splits_corrected,
        'total_splits_reference': total_splits_reference
    }

def create_enhanced_correction():
    """Create an enhanced correction that fixes splits and fuel issues"""
    
    print("\n🔧 CREATING ENHANCED CORRECTION...")
    
    # Load original data and production reference
    original_data = load_json_file('firewood_splitter_data_20251013_141629.json')
    production_ref = load_json_file('production_data copy.json')
    
    if not original_data or not production_ref:
        return None
    
    # Make a deep copy for correction
    corrected_data = json.loads(json.dumps(original_data))
    baskets = corrected_data['basket_history']['completed_baskets']
    ref_baskets = production_ref['completed_baskets']
    
    print(f"Starting with {len(baskets)} baskets")
    
    # Fix basket #2 and #3 merger with correct splits counting
    if len(baskets) >= 3 and len(ref_baskets) >= 3:
        basket_2 = baskets[1]  # Index 1 = basket #2
        basket_3 = baskets[2]  # Index 2 = basket #3
        ref_basket_2 = ref_baskets[1]
        ref_basket_3 = ref_baskets[2]
        
        # Count actual successful splits from reference cycles
        ref_2_splits = len([c for c in ref_basket_2['cycles'] if not c.get('aborted', False)])
        ref_3_splits = len([c for c in ref_basket_3['cycles'] if not c.get('aborted', False)])
        
        print(f"Reference basket #2: {ref_2_splits} splits")
        print(f"Reference basket #3: {ref_3_splits} splits")
        
        # Create properly merged basket
        merged_basket = {
            "basket_number": 2,
            "start_time": basket_2['start_time'],
            "start_time_formatted": basket_2['start_time_formatted'],
            "complete_time": basket_3['complete_time'],
            "complete_time_formatted": basket_3['complete_time_formatted'],
            "duration_seconds": basket_3['complete_time'] - basket_2['start_time'],
            "splits_completed": ref_2_splits + ref_3_splits,  # Use reference counts
            "cycles_attempted": basket_2['cycles_attempted'] + basket_3['cycles_attempted'],
        }
        
        # Calculate derived fields
        merged_basket["duration_formatted"] = f"{merged_basket['duration_seconds']:.1f}s"
        merged_basket["success_rate"] = (merged_basket['splits_completed'] / merged_basket['cycles_attempted']) * 100
        
        # Handle timing fields
        merged_basket["idle_time_seconds"] = basket_2['idle_time_seconds'] + basket_3['idle_time_seconds']
        merged_basket["break_time_seconds"] = basket_2['break_time_seconds'] + basket_3['break_time_seconds']
        merged_basket["operational_time_seconds"] = merged_basket['duration_seconds']
        merged_basket["productive_time_seconds"] = basket_3.get('productive_time_seconds', merged_basket['duration_seconds'])
        merged_basket["active_time_seconds"] = basket_3.get('active_time_seconds', merged_basket['duration_seconds'])
        
        # Calculate percentages
        if merged_basket['duration_seconds'] > 0:
            merged_basket["idle_time_percentage"] = (merged_basket['idle_time_seconds'] / merged_basket['duration_seconds']) * 100
            merged_basket["break_time_percentage"] = (merged_basket['break_time_seconds'] / merged_basket['duration_seconds']) * 100
            merged_basket["operational_time_percentage"] = 100.0
        else:
            merged_basket["idle_time_percentage"] = 0.0
            merged_basket["break_time_percentage"] = 0.0
            merged_basket["operational_time_percentage"] = 0.0
        
        # Fix fuel data - use reference data
        merged_basket["start_fuel_level"] = ref_basket_2.get('start_fuel_level')
        merged_basket["end_fuel_level"] = ref_basket_3.get('end_fuel_level')
        merged_basket["fuel_consumed"] = ref_basket_2.get('fuel_consumed', 0) + ref_basket_3.get('fuel_consumed', 0)
        
        # Calculate splits per gallon
        if merged_basket["fuel_consumed"] > 0:
            merged_basket["splits_per_gallon"] = merged_basket['splits_completed'] / merged_basket["fuel_consumed"]
        else:
            merged_basket["splits_per_gallon"] = 0
        
        print(f"✅ Enhanced merged basket: {merged_basket['splits_completed']} splits, {merged_basket['fuel_consumed']:.3f} gallons")
        
        # Replace baskets 2 and 3 with corrected merged basket
        new_baskets = [baskets[0]]  # Keep basket #1
        new_baskets.append(merged_basket)  # Add corrected merged basket #2
        
        # Add remaining baskets with corrected data and renumbering
        for i in range(3, len(baskets)):  # Start from old basket #4
            basket = baskets[i].copy()
            basket['basket_number'] = i  # Renumber
            
            # Fix splits count using reference data
            if i < len(ref_baskets):
                ref_basket = ref_baskets[i]
                ref_splits = len([c for c in ref_basket['cycles'] if not c.get('aborted', False)])
                basket['splits_completed'] = ref_splits
                
                # Recalculate success rate
                if basket['cycles_attempted'] > 0:
                    basket['success_rate'] = (basket['splits_completed'] / basket['cycles_attempted']) * 100
                
                # Fix fuel data
                basket['fuel_consumed'] = ref_basket.get('fuel_consumed', 0)
                basket['start_fuel_level'] = ref_basket.get('start_fuel_level')
                basket['end_fuel_level'] = ref_basket.get('end_fuel_level')
                
                # Recalculate splits per gallon
                if basket['fuel_consumed'] > 0:
                    basket['splits_per_gallon'] = basket['splits_completed'] / basket['fuel_consumed']
                else:
                    basket['splits_per_gallon'] = 0
            
            new_baskets.append(basket)
        
        # Update the basket list
        corrected_data['basket_history']['completed_baskets'] = new_baskets
        
        # Recalculate cumulative totals with corrected data
        total_splits = sum(b['splits_completed'] for b in new_baskets)
        total_cycles = sum(b['cycles_attempted'] for b in new_baskets)
        total_fuel = sum(b.get('fuel_consumed', 0) for b in new_baskets)
        completed_cycles = total_splits
        aborted_cycles = total_cycles - completed_cycles
        
        # Update current basket number
        if 'current_basket' in corrected_data['basket_history']:
            corrected_data['basket_history']['current_basket']['basket_number'] = len(new_baskets) + 1
        if 'current_basket' in corrected_data:
            corrected_data['current_basket']['basket_number'] = len(new_baskets) + 1
        
        # Update cumulative totals
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
                    'current_basket_splits_per_hour': 0.0,
                    'average_splits_per_basket': total_splits / len(new_baskets) if len(new_baskets) > 0 else 0
                }
        
        # Update basket history totals
        corrected_data['basket_history']['total_baskets_completed'] = len(new_baskets)
        corrected_data['basket_history']['total_fuel_consumed'] = total_fuel
        corrected_data['basket_history']['average_fuel_per_basket'] = total_fuel / len(new_baskets) if len(new_baskets) > 0 else 0
        
        print(f"\n📈 ENHANCED CORRECTED STATISTICS:")
        print(f"   Total Baskets: {len(new_baskets)}")
        print(f"   Total Splits: {total_splits}")
        print(f"   Total Fuel: {total_fuel:.3f} gallons")
        print(f"   Success Rate: {(completed_cycles / total_cycles) * 100:.1f}%")
        
        return corrected_data
    
    return None

def main():
    """Main analysis and correction function"""
    print("🔍 ENHANCED DATA ANALYSIS & CORRECTION")
    print("=" * 60)
    
    # First, analyze current discrepancies
    analysis_result = analyze_data_discrepancies()
    
    if analysis_result:
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Splits issues: {len(analysis_result['splits_issues'])}")
        print(f"   Fuel issues: {len(analysis_result['fuel_issues'])}")
        print(f"   Total splits (corrected): {analysis_result['total_splits_corrected']}")
        print(f"   Total splits (reference): {analysis_result['total_splits_reference']}")
        
        if analysis_result['splits_issues'] or analysis_result['fuel_issues']:
            print("\n🔧 Creating enhanced correction...")
            
            enhanced_data = create_enhanced_correction()
            if enhanced_data:
                # Save enhanced correction
                try:
                    with open('out.json', 'w') as f:
                        json.dump(enhanced_data, f, indent=2)
                    print("\n✅ Enhanced correction saved to out.json")
                except Exception as e:
                    print(f"❌ Failed to save enhanced correction: {e}")
        else:
            print("\n✅ No issues found - current correction is accurate")

if __name__ == "__main__":
    main()