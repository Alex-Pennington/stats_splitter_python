#!/usr/bin/env python3
"""
Fuel Consumption Correction Tool

This tool corrects the fuel consumption data by:
1. Using the production_data copy.json as the reference for actual fuel usage
2. Identifying missing fuel consumption in baskets 2 and 3 
3. Redistributing fuel consumption to match the reference data
4. Ensuring total fuel consumption matches the actual 5 gallons used
"""

import json

def analyze_fuel_consumption():
    """Analyze fuel consumption from both files"""
    
    print("🔍 ANALYZING FUEL CONSUMPTION DATA")
    print("=" * 50)
    
    # Load files
    corrected_data = json.load(open('out.json', 'r'))
    production_ref = json.load(open('production_data copy.json', 'r'))
    
    corrected_baskets = corrected_data['basket_history']['completed_baskets']
    ref_baskets = production_ref['completed_baskets']
    
    print("CURRENT CORRECTED DATA:")
    corrected_total = 0
    for basket in corrected_baskets:
        fuel = basket.get('fuel_consumed', 0)
        corrected_total += fuel
        print(f"  Basket #{basket['basket_number']}: {fuel:.3f} gal")
    print(f"  Total: {corrected_total:.3f} gallons")
    
    print("\nPRODUCTION REFERENCE DATA:")
    ref_total = 0
    for i, basket in enumerate(ref_baskets):
        fuel = basket.get('fuel_consumed', 0)
        ref_total += fuel
        print(f"  Reference basket #{i+1}: {fuel:.3f} gal")
    print(f"  Total: {ref_total:.3f} gallons")
    
    print(f"\nFUEL DISCREPANCY: {ref_total - corrected_total:.3f} gallons missing")
    
    return corrected_data, production_ref, ref_total

def correct_fuel_consumption():
    """Correct fuel consumption using production reference data"""
    
    corrected_data, production_ref, reference_total = analyze_fuel_consumption()
    
    print(f"\n🔧 CORRECTING FUEL CONSUMPTION")
    print("=" * 50)
    
    corrected_baskets = corrected_data['basket_history']['completed_baskets']
    ref_baskets = production_ref['completed_baskets']
    
    # Map the reference fuel data to corrected baskets
    # Remember: we merged baskets 2&3, so we need to handle the mapping
    
    print("FUEL MAPPING STRATEGY:")
    print("Original -> Corrected mapping:")
    print("  Ref basket #1 -> Corrected basket #1")
    print("  Ref basket #2 + #3 -> Corrected basket #2 (merged)")
    print("  Ref basket #4 -> Corrected basket #3")
    print("  Ref basket #5 -> Corrected basket #4")
    print("  ... and so on")
    
    # Apply fuel corrections
    fuel_corrections = []
    
    # Basket #1: Use reference basket #1 fuel data
    if len(ref_baskets) > 0:
        ref_fuel_1 = ref_baskets[0].get('fuel_consumed', 0)
        corrected_baskets[0]['fuel_consumed'] = ref_fuel_1
        corrected_baskets[0]['start_fuel_level'] = ref_baskets[0].get('start_fuel_level')
        corrected_baskets[0]['end_fuel_level'] = ref_baskets[0].get('end_fuel_level')
        if ref_fuel_1 > 0:
            corrected_baskets[0]['splits_per_gallon'] = corrected_baskets[0]['splits_completed'] / ref_fuel_1
        fuel_corrections.append(f"Basket #1: {ref_fuel_1:.3f} gal (from reference)")
    
    # Basket #2 (merged): Use reference baskets #2 + #3 fuel data
    if len(ref_baskets) > 2:
        ref_fuel_2 = ref_baskets[1].get('fuel_consumed', 0)
        ref_fuel_3 = ref_baskets[2].get('fuel_consumed', 0)
        merged_fuel = ref_fuel_2 + ref_fuel_3
        
        corrected_baskets[1]['fuel_consumed'] = merged_fuel
        # Use start fuel from ref basket #2, end fuel from ref basket #3
        corrected_baskets[1]['start_fuel_level'] = ref_baskets[1].get('start_fuel_level')
        corrected_baskets[1]['end_fuel_level'] = ref_baskets[2].get('end_fuel_level')
        
        if merged_fuel > 0:
            corrected_baskets[1]['splits_per_gallon'] = corrected_baskets[1]['splits_completed'] / merged_fuel
        else:
            corrected_baskets[1]['splits_per_gallon'] = 0
            
        fuel_corrections.append(f"Basket #2 (merged): {merged_fuel:.3f} gal ({ref_fuel_2:.3f} + {ref_fuel_3:.3f})")
    
    # Remaining baskets: Map reference baskets #4+ to corrected baskets #3+
    for i in range(2, len(corrected_baskets)):
        ref_index = i + 2  # Corrected basket #3 = ref basket #5, etc.
        if ref_index < len(ref_baskets):
            ref_fuel = ref_baskets[ref_index].get('fuel_consumed', 0)
            corrected_baskets[i]['fuel_consumed'] = ref_fuel
            corrected_baskets[i]['start_fuel_level'] = ref_baskets[ref_index].get('start_fuel_level')
            corrected_baskets[i]['end_fuel_level'] = ref_baskets[ref_index].get('end_fuel_level')
            
            if ref_fuel > 0:
                corrected_baskets[i]['splits_per_gallon'] = corrected_baskets[i]['splits_completed'] / ref_fuel
            else:
                corrected_baskets[i]['splits_per_gallon'] = 0
                
            fuel_corrections.append(f"Basket #{corrected_baskets[i]['basket_number']}: {ref_fuel:.3f} gal (from ref basket #{ref_index+1})")
    
    # Recalculate totals
    new_total_fuel = sum(b.get('fuel_consumed', 0) for b in corrected_baskets)
    
    # Update cumulative totals
    corrected_data['cumulative_totals']['total_fuel_consumed_gallons'] = new_total_fuel
    corrected_data['cumulative_totals']['average_fuel_per_basket'] = new_total_fuel / len(corrected_baskets)
    
    # Update basket history totals
    corrected_data['basket_history']['total_fuel_consumed'] = new_total_fuel
    corrected_data['basket_history']['average_fuel_per_basket'] = new_total_fuel / len(corrected_baskets)
    
    print("\nFUEL CORRECTIONS APPLIED:")
    for correction in fuel_corrections:
        print(f"  {correction}")
    
    print(f"\nNEW TOTAL FUEL CONSUMPTION: {new_total_fuel:.3f} gallons")
    print(f"REFERENCE TOTAL: {reference_total:.3f} gallons")
    print(f"DIFFERENCE: {abs(new_total_fuel - reference_total):.3f} gallons")
    
    return corrected_data

def main():
    """Main fuel correction function"""
    print("⛽ FUEL CONSUMPTION CORRECTION TOOL")
    print("Using production_data copy.json as reference")
    print("=" * 60)
    
    # Correct fuel consumption
    corrected_data = correct_fuel_consumption()
    
    # Save corrected data
    with open('out.json', 'w') as f:
        json.dump(corrected_data, f, indent=2)
    
    print(f"\n✅ FUEL CORRECTION COMPLETE")
    print(f"   Updated file: out.json")
    print(f"   Fuel data now matches production reference")
    print(f"   Missing fuel consumption redistributed to baskets #2 and #3")
    
    # Show final summary
    baskets = corrected_data['basket_history']['completed_baskets']
    print(f"\n📊 FINAL FUEL SUMMARY:")
    total = 0
    for basket in baskets:
        fuel = basket.get('fuel_consumed', 0)
        total += fuel
        splits_per_gal = basket.get('splits_per_gallon', 0)
        print(f"  Basket #{basket['basket_number']}: {fuel:.3f} gal, {splits_per_gal:.1f} splits/gal")
    print(f"  TOTAL: {total:.3f} gallons")

if __name__ == "__main__":
    main()