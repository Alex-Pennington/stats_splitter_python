import json

with open('production_data.json', 'r') as f:
    data = json.load(f)

print('=== BASKET 1 (completed) ===')
b1 = data['completed_baskets'][0]
print(f'Total cycles in basket 1: {len(b1["cycles"])}')
print(f'Complete splits in basket 1: {len([c for c in b1["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])}')
print(f'Start time: {b1["start_time"]}')
print(f'Complete time: {b1["complete_time"]}')

print()
print('=== BASKET 2 (completed) ===')
b2 = data['completed_baskets'][1]
print(f'Total cycles in basket 2: {len(b2["cycles"])}')
print(f'Complete splits in basket 2: {len([c for c in b2["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])}')
print(f'Start time: {b2["start_time"]}')
print(f'Complete time: {b2["complete_time"]}')

print()
print('=== CURRENT BASKET ===')
cb = data['current_basket']
print(f'Total cycles in current: {len(cb["cycles"])}')
print(f'Complete splits in current: {len([c for c in cb["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])}')
print(f'Start time: {cb["start_time"]}')
print(f'Is active: {cb["is_currently_active"]}')

print()
print('=== SESSION TOTALS ===')
print(f'Total splits: {data["total_splits"]}')
print(f'Total cycles: {data["total_cycles"]}')
print(f'Total baskets: {data["total_baskets"]}')

print()
print('=== CALCULATED TOTALS ===')
basket1_splits = len([c for c in b1["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])
basket2_splits = len([c for c in b2["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])
current_splits = len([c for c in cb["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])
print(f'Basket 1 splits: {basket1_splits}')
print(f'Basket 2 splits: {basket2_splits}')
print(f'Current basket splits: {current_splits}')
print(f'Sum of all splits: {basket1_splits + basket2_splits + current_splits}')
print(f'Session total_splits: {data["total_splits"]}')
print(f'Match: {basket1_splits + basket2_splits + current_splits == data["total_splits"]}')
