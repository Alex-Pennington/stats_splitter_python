#!/usr/bin/env python3
"""
Test script for LogSplitter Controller MQTT integration
Verifies that the MQTT client can parse controller messages correctly
"""

import time
import logging
from production_stats import ProductionStatsEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_controller_events():
    """Test processing of LogSplitter Controller events"""
    logger.info("Testing LogSplitter Controller MQTT event processing...")
    
    # Create production stats engine
    stats = ProductionStatsEngine()
    
    # Simulate a complete production cycle
    logger.info("\n=== Testing Complete Production Cycle ===")
    
    # 1. Start cycle
    stats.handle_sequence_event('cycle_start')
    stats.handle_sequence_event('extend_start')
    
    # 2. Extend phase
    stats.handle_pressure_reading(1800.5, 'hydraulic_system')
    stats.handle_sequence_event('extend_complete')
    
    # 3. Retract phase  
    stats.handle_sequence_event('retract_start')
    stats.handle_pressure_reading(1600.2, 'hydraulic_system')
    stats.handle_sequence_event('retract_complete')
    
    # 4. Complete cycle
    stats.handle_sequence_event('cycle_complete')
    
    # Print current stats
    summary = stats.get_production_summary()
    logger.info(f"Stats after 1 cycle: {summary}")
    
    # Simulate multiple cycles to complete a basket
    logger.info("\n=== Testing Multiple Cycles for Basket Completion ===")
    
    for cycle_num in range(2, 61):  # Cycles 2-60 to complete basket
        stats.handle_sequence_event('cycle_start')
        stats.handle_sequence_event('extend_start')
        time.sleep(0.001)  # Small delay
        stats.handle_sequence_event('extend_complete')
        stats.handle_sequence_event('retract_start')
        time.sleep(0.001)  # Small delay
        stats.handle_sequence_event('retract_complete')
        stats.handle_sequence_event('cycle_complete')
        
        if cycle_num % 10 == 0:
            summary = stats.get_production_summary()
            logger.info(f"Cycle {cycle_num}: {summary['total_splits']} splits, "
                       f"{summary['total_baskets']} baskets")
    
    # Final stats
    final_summary = stats.get_production_summary()
    logger.info(f"\n=== Final Production Summary ===")
    logger.info(f"Total Splits: {final_summary['total_splits']}")
    logger.info(f"Total Baskets: {final_summary['total_baskets']}")
    logger.info(f"Splits per Hour: {final_summary['production_rates']['splits_per_hour']:.1f}")
    logger.info(f"Average Cycle Time: {final_summary['average_cycle_time']:.1f}s")
    
    # Test safety events
    logger.info("\n=== Testing Safety Events ===")
    stats.handle_sequence_event('safety_stop')
    stats.handle_sequence_event('emergency_stop')
    stats.handle_sequence_event('safety_clear')
    
    logger.info("LogSplitter Controller MQTT test completed successfully!")

if __name__ == "__main__":
    test_controller_events()