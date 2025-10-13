#!/usr/bin/env python3
"""
Enhanced Fuel Correction Tool

Since the production reference also shows missing fuel data for baskets 2&3,
we need to:
1. Recognize that 5 gallons total was used during the day
2. Estimate and redistribute the missing 1.29 gallons to baskets 2&3
3. Base the distribution on operational time and splits completed
"""

import json

def estimate_missing_fuel():
    """Estimate and redistribute missing fuel consumption"""
    
    print("⛽ ENHANCED FUEL CORRECTION")
    print("Addressing missing fuel data in baskets 2 & 3")
    print("=" * 50)
    
    # Load corrected data
    corrected_data = json.load(open('out.json', 'r'))
    baskets = corrected_data['basket_history']['completed_baskets']
    
    # Calculate current fuel total
    current_total = sum(b.get('fuel_consumed', 0) for b in baskets)
    target_total = 5.0  # 5 gallons total for the day
    missing_fuel = target_total - current_total
    
    print(f"Current fuel total: {current_total:.3f} gallons")
    print(f"Target fuel total: {target_total:.3f} gallons")
    print(f"Missing fuel: {missing_fuel:.3f} gallons")
    
    # Find baskets 2 and 3 (indices 1 and 2)
    basket_2 = baskets[1]  # Merged basket
    basket_3 = baskets[2]  # Current basket #3
    
    print(f"\nBaskets with missing fuel data:")
    print(f"  Basket #2 (merged): {basket_2['splits_completed']} splits, {basket_2['duration_seconds']/60:.1f} min")
    print(f"  Basket #3: {basket_3['splits_completed']} splits, {basket_3['duration_seconds']/60:.1f} min")
    
    # Estimate fuel distribution based on operational characteristics
    # Use a combination of duration and splits completed as factors
    
    basket_2_duration = basket_2['duration_seconds']
    basket_3_duration = basket_3['duration_seconds']
    basket_2_splits = basket_2['splits_completed']
    basket_3_splits = basket_3['splits_completed']
    
    # Weight by both duration and splits (more work = more fuel)
    basket_2_weight = (basket_2_duration * 0.6) + (basket_2_splits * 0.4)
    basket_3_weight = (basket_3_duration * 0.6) + (basket_3_splits * 0.4)
    total_weight = basket_2_weight + basket_3_weight
    
    # Distribute missing fuel proportionally
    basket_2_fuel = missing_fuel * (basket_2_weight / total_weight)
    basket_3_fuel = missing_fuel * (basket_3_weight / total_weight)
    
    print(f"\nFuel distribution calculation:")
    print(f"  Basket #2 weight: {basket_2_weight:.1f} (duration: {basket_2_duration:.0f}s, splits: {basket_2_splits})")
    print(f"  Basket #3 weight: {basket_3_weight:.1f} (duration: {basket_3_duration:.0f}s, splits: {basket_3_splits})")
    print(f"  Basket #2 fuel estimate: {basket_2_fuel:.3f} gallons")
    print(f"  Basket #3 fuel estimate: {basket_3_fuel:.3f} gallons")
    
    # Apply fuel corrections
    basket_2['fuel_consumed'] = basket_2_fuel
    basket_3['fuel_consumed'] = basket_3_fuel
    
    # Estimate fuel levels for basket #2 (merged)
    # Start from end of basket #1, subtract fuel used
    basket_1_end = baskets[0].get('end_fuel_level', 4.26)
    basket_2['start_fuel_level'] = basket_1_end
    basket_2['end_fuel_level'] = basket_1_end - basket_2_fuel
    
    # Estimate fuel levels for basket #3 
    basket_3['start_fuel_level'] = basket_2['end_fuel_level']
    basket_3['end_fuel_level'] = basket_3['start_fuel_level'] - basket_3_fuel
    
    # Calculate splits per gallon
    basket_2['splits_per_gallon'] = basket_2_splits / basket_2_fuel if basket_2_fuel > 0 else 0
    basket_3['splits_per_gallon'] = basket_3_splits / basket_3_fuel if basket_3_fuel > 0 else 0
    
    # Adjust subsequent baskets' start fuel levels
    for i in range(3, len(baskets)):
        prev_basket = baskets[i-1]
        current_basket = baskets[i]
        
        # If the basket doesn't have start fuel level, estimate it
        if current_basket.get('start_fuel_level') is None:
            current_basket['start_fuel_level'] = prev_basket.get('end_fuel_level')
        
        # If the basket doesn't have end fuel level, calculate it
        if current_basket.get('end_fuel_level') is None:
            fuel_consumed = current_basket.get('fuel_consumed', 0)
            current_basket['end_fuel_level'] = current_basket['start_fuel_level'] - fuel_consumed
    
    # Recalculate totals
    new_total_fuel = sum(b.get('fuel_consumed', 0) for b in baskets)
    
    # Update cumulative totals
    corrected_data['cumulative_totals']['total_fuel_consumed_gallons'] = new_total_fuel
    corrected_data['cumulative_totals']['average_fuel_per_basket'] = new_total_fuel / len(baskets)
    
    # Update basket history totals
    corrected_data['basket_history']['total_fuel_consumed'] = new_total_fuel
    corrected_data['basket_history']['average_fuel_per_basket'] = new_total_fuel / len(baskets)
    
    print(f"\n✅ FUEL CORRECTIONS APPLIED:")
    print(f"  Basket #2: {basket_2_fuel:.3f} gal, {basket_2['splits_per_gallon']:.1f} splits/gal")
    print(f"  Basket #3: {basket_3_fuel:.3f} gal, {basket_3['splits_per_gallon']:.1f} splits/gal")
    print(f"  New total: {new_total_fuel:.3f} gallons (target: {target_total:.3f})")
    
    return corrected_data

def main():
    """Main enhanced fuel correction"""
    corrected_data = estimate_missing_fuel()
    
    # Save corrected data
    with open('out.json', 'w') as f:
        json.dump(corrected_data, f, indent=2)
    
    print(f"\n🎯 ENHANCED FUEL CORRECTION COMPLETE")
    print(f"   File updated: out.json")
    print(f"   Missing fuel redistributed based on operational load")
    print(f"   Total fuel consumption now matches daily usage of ~5.0 gallons")
    
    # Final summary
    baskets = corrected_data['basket_history']['completed_baskets']
    print(f"\n📊 CORRECTED FUEL SUMMARY:")
    total = 0
    for basket in baskets:
        fuel = basket.get('fuel_consumed', 0)
        total += fuel
        splits_per_gal = basket.get('splits_per_gallon', 0)
        start_fuel = basket.get('start_fuel_level', 'N/A')
        end_fuel = basket.get('end_fuel_level', 'N/A')
        print(f"  Basket #{basket['basket_number']}: {fuel:.3f} gal, {splits_per_gal:.1f} splits/gal ({start_fuel} → {end_fuel})")
    print(f"  TOTAL: {total:.3f} gallons")
    
    print(f"\n💡 OPERATOR INSIGHTS:")
    print(f"   • Basket #2 (merged): Consumed ~{baskets[1]['fuel_consumed']:.2f} gal over 41 minutes")
    print(f"   • Basket #3: Consumed ~{baskets[2]['fuel_consumed']:.2f} gal over 48 minutes") 
    print(f"   • These estimates help track fuel efficiency during the period")
    print(f"     when fuel monitoring was disrupted by the duplicate basket signal")

if __name__ == "__main__":
    main()