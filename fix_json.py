#!/usr/bin/env python3
"""
Script to fix the duplicate basket data in production_data.json
"""
import json
import shutil
from datetime import datetime

def fix_production_data():
    # Backup the original file
    backup_file = "production_data_backup.json"
    shutil.copy("production_data.json", backup_file)
    print(f"Backed up original file to {backup_file}")
    
    try:
        # Try to load the JSON (it will likely fail due to malformed structure)
        with open("production_data.json", "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Let's rebuild the JSON structure manually
    # We know the structure should be:
    # - Basic stats
    # - completed_baskets (array with 3 unique baskets)
    # - current_basket (the basket with start_time 1760291110.5755997)
    
    print("Attempting to rebuild clean JSON structure...")
    
    # Read the backup to extract the valid data sections
    try:
        # Extract the completed baskets data up to the first occurrence of the duplicate
        lines = content.split('\n')
        
        # Find where completed_baskets section starts and extract valid baskets
        start_collecting = False
        basket_count = 0
        completed_baskets = []
        current_basket = None
        
        # Find the proper current basket data (with start_time 1760291110.5755997)
        current_basket_start_idx = content.find('"start_time": 1760291110.5755997')
        if current_basket_start_idx == -1:
            print("Could not find current basket start time")
            return False
            
        # Let's try a simpler approach - manually construct the clean data
        clean_data = {
            "start_time": 1760280748.2111413,
            "total_cycles": 355,  # Updated count
            "total_splits": 321,  # Updated count
            "total_baskets": 3,
            "last_activity_time": 1760291382.4869692,
            "completed_baskets": [],
            "current_basket": {
                "start_time": 1760291110.5755997,
                "complete_time": None,
                "exchange_time": None,
                "start_fuel_level": 2.5,
                "end_fuel_level": None,
                "fuel_consumed": 0.0,
                "idle_time": 0.14249563217163086,
                "break_time": 0.0,
                "on_break": False,
                "break_start_time": None,
                "last_activity_time": 1760291382.4869692,
                "is_currently_active": True,
                "cycles": []
            }
        }
        
        print("Clean structure created, will need to extract basket and cycle data manually")
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

if __name__ == "__main__":
    fix_production_data()