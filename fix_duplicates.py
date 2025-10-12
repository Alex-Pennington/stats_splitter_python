#!/usr/bin/env python3
"""
Fix duplicate baskets in production_data.json
"""
import json
import os

def fix_duplicate_baskets():
    """Remove duplicate baskets from production data"""
    try:
        # Load current data
        with open('production_data.json', 'r') as f:
            data = json.load(f)
        
        print("Original data:")
        completed_baskets = data.get('completed_baskets', [])
        print(f"Completed baskets: {len(completed_baskets)}")
        
        # Check for duplicates in completed baskets
        unique_baskets = []
        seen_start_times = set()
        duplicates_found = 0
        
        for i, basket in enumerate(completed_baskets):
            start_time = basket.get('start_time')
            if start_time not in seen_start_times:
                unique_baskets.append(basket)
                seen_start_times.add(start_time)
                print(f"Basket {i+1}: Kept (start_time: {start_time})")
            else:
                duplicates_found += 1
                print(f"Basket {i+1}: DUPLICATE REMOVED (start_time: {start_time})")
        
        # Update data with unique baskets
        data['completed_baskets'] = unique_baskets
        data['total_baskets'] = len(unique_baskets)
        
        # Backup original file
        os.rename('production_data.json', 'production_data_backup.json')
        print("Created backup: production_data_backup.json")
        
        # Save fixed data
        with open('production_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nFixed data:")
        print(f"  Original baskets: {len(completed_baskets)}")
        print(f"  Duplicates removed: {duplicates_found}")
        print(f"  Final unique baskets: {len(unique_baskets)}")
        print("  File updated successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error fixing duplicate baskets: {e}")
        return False

if __name__ == "__main__":
    fix_duplicate_baskets()