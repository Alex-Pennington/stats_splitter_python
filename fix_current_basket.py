#!/usr/bin/env python3
"""
Fix the current_basket duplication issue
"""
import json
import os

def fix_current_basket_duplication():
    """Fix current basket that should have been cleared after completion"""
    try:
        # Load current data
        with open('production_data.json', 'r') as f:
            data = json.load(f)
        
        print("Checking current_basket status...")
        current_basket = data.get('current_basket')
        completed_baskets = data.get('completed_baskets', [])
        
        if current_basket:
            current_start_time = current_basket.get('start_time')
            current_complete_time = current_basket.get('complete_time')
            
            print(f"Current basket start_time: {current_start_time}")
            print(f"Current basket complete_time: {current_complete_time}")
            print(f"Current basket is completed: {current_complete_time is not None}")
            
            # Check if current basket is already in completed baskets
            duplicate_found = False
            for basket in completed_baskets:
                if basket.get('start_time') == current_start_time:
                    duplicate_found = True
                    print(f"DUPLICATE FOUND: Current basket is already in completed_baskets")
                    break
            
            if duplicate_found and current_complete_time is not None:
                print("Fixing: Clearing current_basket since it's completed and duplicated")
                data['current_basket'] = None
                
                # Create backup
                os.rename('production_data.json', 'production_data_backup2.json')
                print("Created backup: production_data_backup2.json")
                
                # Save fixed data
                with open('production_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("✅ Fixed: current_basket cleared, duplication resolved!")
                return True
            else:
                print("No fix needed: current_basket is either unique or not completed")
                return False
        else:
            print("No current_basket found")
            return False
        
    except Exception as e:
        print(f"Error fixing current basket duplication: {e}")
        return False

if __name__ == "__main__":
    fix_current_basket_duplication()