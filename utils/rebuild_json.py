#!/usr/bin/env python3
"""
Script to extract and rebuild valid production data from malformed JSON
"""
import re
import json

def extract_valid_data():
    """Extract valid data sections from the malformed JSON"""
    
    with open("production_data.json", "r") as f:
        content = f.read()
    
    # Extract the basic stats from the beginning
    basic_stats = {}
    
    # Use regex to find the basic stats
    basic_patterns = {
        'start_time': r'"start_time":\s*([0-9.]+)',
        'total_cycles': r'"total_cycles":\s*(\d+)',
        'total_splits': r'"total_splits":\s*(\d+)', 
        'total_baskets': r'"total_baskets":\s*(\d+)',
        'last_activity_time': r'"last_activity_time":\s*([0-9.]+)'
    }
    
    for key, pattern in basic_patterns.items():
        match = re.search(pattern, content)
        if match:
            if key in ['total_cycles', 'total_splits', 'total_baskets']:
                basic_stats[key] = int(match.group(1))
            else:
                basic_stats[key] = float(match.group(1))
    
    print("Extracted basic stats:", basic_stats)
    
    # Find all basket start times to identify unique baskets
    basket_starts = re.findall(r'"start_time":\s*([0-9.]+)', content)
    print(f"Found {len(basket_starts)} start times")
    
    # Remove duplicates and get unique basket start times
    unique_starts = []
    seen = set()
    for start in basket_starts:
        if start not in seen and start != str(basic_stats['start_time']):
            unique_starts.append(float(start))
            seen.add(start)
    
    unique_starts.sort()
    print(f"Unique basket start times: {unique_starts}")
    
    # The current basket should be the latest one: 1760291110.5755997
    current_basket_time = 1760291110.5755997
    completed_basket_times = [t for t in unique_starts if t != current_basket_time]
    
    print(f"Completed basket times: {completed_basket_times}")
    print(f"Current basket time: {current_basket_time}")
    
    # Create minimal valid structure for now
    clean_data = {
        "start_time": basic_stats['start_time'],
        "total_cycles": basic_stats['total_cycles'], 
        "total_splits": basic_stats['total_splits'],
        "total_baskets": 3,  # We know we have 3 completed baskets
        "last_activity_time": basic_stats['last_activity_time'],
        "completed_baskets": [
            # We'll need to extract these manually - for now create minimal entries
            {
                "start_time": 1760280748.2111413,
                "complete_time": 1760282862.0959566,
                "exchange_time": 1760282862.0959566,
                "start_fuel_level": 4.63,
                "end_fuel_level": 4.3,
                "fuel_consumed": 0.33,
                "idle_time": 0.0,
                "break_time": 0.0,
                "on_break": False,
                "break_start_time": None,
                "last_activity_time": None,
                "is_currently_active": False,
                "cycles": []
            },
            {
                "start_time": 1760282862.1033418,
                "complete_time": 1760286957.5646431,
                "exchange_time": 1760286957.5646431,
                "start_fuel_level": 4.3,
                "end_fuel_level": 3.41,
                "fuel_consumed": 0.89,
                "idle_time": 0.0,
                "break_time": 0.0,
                "on_break": False,
                "break_start_time": None,
                "last_activity_time": None,
                "is_currently_active": False,
                "cycles": []
            },
            {
                "start_time": 1760286957.5866432,
                "complete_time": 1760289853.3369372,
                "exchange_time": 1760289853.3369372,
                "start_fuel_level": 3.41,
                "end_fuel_level": 2.77,
                "fuel_consumed": 0.64,
                "idle_time": 1828.37,
                "break_time": 0.0,
                "on_break": False,
                "break_start_time": None,
                "last_activity_time": 1760290915.4088252,
                "is_currently_active": False,
                "cycles": []
            }
        ],
        "current_basket": {
            "start_time": 1760291110.5755997,
            "complete_time": None,
            "exchange_time": None,
            "start_fuel_level": 2.5,
            "end_fuel_level": None,
            "fuel_consumed": 0.0,
            "idle_time": 271.72,  # Approximate based on current time
            "break_time": 0.0,
            "on_break": False,
            "break_start_time": None,
            "last_activity_time": basic_stats['last_activity_time'],
            "is_currently_active": True,
            "cycles": []
        }
    }
    
    # Write the clean data
    with open("production_data_clean.json", "w") as f:
        json.dump(clean_data, f, indent=2)
    
    print("Clean data written to production_data_clean.json")
    return True

if __name__ == "__main__":
    extract_valid_data()