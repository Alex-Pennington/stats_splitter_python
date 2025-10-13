import json

with open('production_data.json', 'r') as f:
    data = json.load(f)

print('=== BASKET EXCHANGE ANALYSIS ===\n')

print(f'Total baskets tracked: {data["total_baskets"]}')
print(f'Completed baskets in array: {len(data["completed_baskets"])}')
print()

for i, basket in enumerate(data['completed_baskets'], 1):
    print(f'BASKET {i}:')
    print(f'  Start time: {basket["start_time"]}')
    print(f'  Complete time: {basket["complete_time"]}')
    print(f'  Exchange time: {basket.get("exchange_time", "NOT SET")}')
    print(f'  Cycles: {len(basket["cycles"])}')
    print(f'  Complete splits: {len([c for c in basket["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])}')
    print(f'  Duration: {basket["complete_time"] - basket["start_time"] if basket["complete_time"] else "N/A":.2f}s')
    print()

print('CURRENT BASKET:')
cb = data['current_basket']
if cb:
    print(f'  Start time: {cb["start_time"]}')
    print(f'  Complete time: {cb.get("complete_time", "NOT SET")}')
    print(f'  Exchange time: {cb.get("exchange_time", "NOT SET")}')
    print(f'  Cycles: {len(cb["cycles"])}')
    print(f'  Complete splits: {len([c for c in cb["cycles"] if c["complete_time"] is not None and not c.get("aborted", False)])}')
    print(f'  Is active: {cb.get("is_currently_active", "unknown")}')
else:
    print('  No current basket')

print()
print('=== EXCHANGE TIME VERIFICATION ===')
exchange_count = 0
for i, basket in enumerate(data['completed_baskets'], 1):
    has_exchange = basket.get('exchange_time') is not None
    exchange_count += 1 if has_exchange else 0
    print(f'Basket {i}: Exchange time {"SET" if has_exchange else "NOT SET"}')

print()
print(f'Baskets with exchange_time set: {exchange_count}/{len(data["completed_baskets"])}')
print(f'Total baskets counter: {data["total_baskets"]}')
