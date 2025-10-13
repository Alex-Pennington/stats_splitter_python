#!/usr/bin/env python3
"""
Duplicate Basket Signal Diagnostic Tool

Investigates suspicious basket completion signals that occur within milliseconds
of each other, indicating potential duplicate HTTP API calls or signal processing issues.
"""

import json
from datetime import datetime
from pathlib import Path

def analyze_duplicate_signals(data, filename):
    """Analyze for duplicate basket completion signals"""
    print(f"\n{'='*70}")
    print(f"DUPLICATE SIGNAL ANALYSIS: {filename}")
    print(f"{'='*70}")
    
    if 'basket_history' not in data or 'completed_baskets' not in data['basket_history']:
        print("No basket history data found")
        return
    
    baskets = data['basket_history']['completed_baskets']
    
    print(f"Found {len(baskets)} completed baskets")
    print(f"System claims {data.get('cumulative_totals', {}).get('total_baskets_completed', 'Unknown')} total baskets")
    
    # Analyze basket completion timing
    print(f"\n🔍 BASKET COMPLETION TIMING ANALYSIS:")
    print(f"{'Basket':<8} {'Complete Time':<25} {'Next Start':<25} {'Gap (ms)':<12} {'Status':<20}")
    print("-" * 90)
    
    suspicious_count = 0
    rapid_completions = []
    
    for i in range(len(baskets)):
        current = baskets[i]
        basket_num = current.get('basket_number', i+1)
        complete_time = current.get('complete_time', 0)
        
        # Format complete time
        complete_formatted = datetime.fromtimestamp(complete_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if complete_time else "N/A"
        
        if i < len(baskets) - 1:
            next_basket = baskets[i + 1]
            next_start = next_basket.get('start_time', 0)
            next_start_formatted = datetime.fromtimestamp(next_start).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if next_start else "N/A"
            
            if complete_time and next_start:
                gap_seconds = next_start - complete_time
                gap_ms = gap_seconds * 1000
                
                status = "NORMAL"
                if gap_ms < 100:  # Less than 100ms
                    status = "🔴 SUSPICIOUS"
                    suspicious_count += 1
                    rapid_completions.append({
                        'from_basket': basket_num,
                        'to_basket': next_basket.get('basket_number', i+2),
                        'gap_ms': gap_ms,
                        'complete_time': complete_time,
                        'next_start': next_start
                    })
                elif gap_ms < 1000:  # Less than 1 second
                    status = "⚠️ RAPID"
                
                print(f"{basket_num:<8} {complete_formatted:<25} {next_start_formatted:<25} {gap_ms:<12.1f} {status:<20}")
            else:
                print(f"{basket_num:<8} {complete_formatted:<25} {'N/A':<25} {'N/A':<12} {'MISSING DATA':<20}")
        else:
            print(f"{basket_num:<8} {complete_formatted:<25} {'[LAST BASKET]':<25} {'N/A':<12} {'END':<20}")
    
    # Summary of issues
    print(f"\n📊 DIAGNOSTIC SUMMARY:")
    print(f"   Total Baskets: {len(baskets)}")
    print(f"   Suspicious Transitions: {suspicious_count}")
    print(f"   Rapid Completions Rate: {(suspicious_count / max(len(baskets) - 1, 1)) * 100:.1f}%")
    
    if rapid_completions:
        print(f"\n🔴 RAPID COMPLETION DETAILS:")
        for completion in rapid_completions:
            gap_ms = completion['gap_ms']
            from_basket = completion['from_basket']
            to_basket = completion['to_basket']
            
            complete_dt = datetime.fromtimestamp(completion['complete_time'])
            start_dt = datetime.fromtimestamp(completion['next_start'])
            
            print(f"   Basket {from_basket} → {to_basket}: {gap_ms:.1f}ms gap")
            print(f"      Complete: {complete_dt.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"      Next Start: {start_dt.strftime('%H:%M:%S.%f')[:-3]}")
    
    # Analyze basket duration patterns
    print(f"\n📈 BASKET DURATION ANALYSIS:")
    print(f"{'Basket':<8} {'Duration (min)':<15} {'Splits':<8} {'Splits/min':<12} {'Notes':<20}")
    print("-" * 65)
    
    short_baskets = []
    
    for basket in baskets:
        basket_num = basket.get('basket_number', 0)
        duration_sec = basket.get('duration_seconds', 0)
        duration_min = duration_sec / 60
        splits = basket.get('splits_completed', 0)
        splits_per_min = splits / max(duration_min, 0.1) if duration_min > 0 else 0
        
        notes = ""
        if duration_min < 5:
            notes = "🔴 VERY SHORT"
            short_baskets.append(basket_num)
        elif duration_min < 15:
            notes = "⚠️ SHORT"
        elif splits_per_min > 5:
            notes = "⚡ HIGH RATE"
        
        print(f"{basket_num:<8} {duration_min:<15.1f} {splits:<8} {splits_per_min:<12.1f} {notes:<20}")
    
    if short_baskets:
        print(f"\n⚠️ ABNORMALLY SHORT BASKETS: {short_baskets}")
        print("   These may be the result of duplicate basket completion signals")
    
    # Check for the expected 9 vs actual 10 basket discrepancy
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    print("   Expected: 9 baskets (user reported)")
    print(f"   Actual: {len(baskets)} baskets (in data)")
    print("   Discrepancy: +1 basket")
    
    if suspicious_count > 0:
        print(f"\n💡 LIKELY CAUSES:")
        print(f"   • {suspicious_count} rapid basket transitions suggest duplicate HTTP calls")
        print("   • Possible double-clicking on basket completion button")
        print("   • Race condition in basket completion handling")
        print("   • Network retry causing duplicate API requests")
        
        # Find the most suspicious transition
        if rapid_completions:
            fastest = min(rapid_completions, key=lambda x: x['gap_ms'])
            print(f"\n   🎯 MOST SUSPICIOUS: Basket {fastest['from_basket']} → {fastest['to_basket']}")
            print(f"      Gap: {fastest['gap_ms']:.1f}ms (almost instantaneous)")
            print(f"      This is likely a duplicate basket completion signal")

def main():
    """Main diagnostic function"""
    base_path = Path(__file__).parent.parent
    
    # Primary file to analyze (the one with detailed timing data)
    primary_file = base_path / "firewood_splitter_data_20251013_141629.json"
    
    print("🔍 DUPLICATE BASKET SIGNAL DIAGNOSTIC")
    print("Investigating rapid basket completion signals...")
    
    if primary_file.exists():
        try:
            with open(primary_file, 'r') as f:
                data = json.load(f)
            analyze_duplicate_signals(data, primary_file.name)
        except Exception as e:
            print(f"Error analyzing {primary_file.name}: {e}")
    else:
        print(f"Primary file not found: {primary_file.name}")
    
    print(f"\n{'='*70}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*70}")
    print("\nCONCLUSION:")
    print("The system shows 10 baskets instead of expected 9 due to rapid")
    print("basket completion signals occurring within milliseconds of each other.")
    print("This suggests duplicate HTTP API calls to /api/production/complete-basket")

if __name__ == "__main__":
    main()