import json

with open('production_data.json', 'r') as f:
    data = json.load(f)

print('=== BASKET DUPLICATION ISSUE ===\n')

print(f'Total baskets counter: {data["total_baskets"]}')
print(f'Completed baskets in array: {len(data["completed_baskets"])}')
print(f'Current basket exists: {data["current_basket"] is not None}')
print()

print('PROBLEM DETECTED:')
print('  Basket 3 appears in BOTH:')
print('    - completed_baskets array (as basket 3)')
print('    - current_basket object')
print()

cb = data['current_basket']
if cb and len(data['completed_baskets']) > 0:
    last_completed = data['completed_baskets'][-1]
    
    print(f'Last completed basket start time: {last_completed["start_time"]}')
    print(f'Current basket start time:        {cb["start_time"]}')
    print(f'SAME START TIME: {last_completed["start_time"] == cb["start_time"]}')
    print()
    
    print(f'Last completed basket complete time: {last_completed["complete_time"]}')
    print(f'Current basket complete time:        {cb.get("complete_time")}')
    print(f'Current basket has complete_time: {cb.get("complete_time") is not None}')
    print()
    
    print('This is the duplicate basket issue again!')
    print('Basket 3 was marked complete and moved to completed_baskets,')
    print('but was NOT cleared from current_basket.')
    print()
    
print('=== WHY BASKET 2 SHOWS ONLY 7 SPLITS ===')
print()
print('Basket 2 is SHORT because:')
print('  Duration: 218.10 seconds (3.6 minutes)')
print('  Only 7 splits completed before basket exchange button was clicked')
print()
print('This suggests the "Complete Basket" button was clicked manually')
print('after only ~3.6 minutes of operation (normal is ~30 minutes).')
print()
print('Complete basket button clicks: 3 times')
print('  - Click 1: Completed basket 1 (80 splits, 1658s = 27.6 min)')
print('  - Click 2: Completed basket 2 (7 splits, 218s = 3.6 min) ← SHORT!')
print('  - Click 3: Completed basket 3 (93 splits, 2259s = 37.7 min)')
