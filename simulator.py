#!/usr/bin/env python3
"""
Firewood Splitter Simulator - Farm Data Accurate

Simulates realistic MQTT messages from a firewood splitter controller
based on REAL FARM DATA patterns:
- Extend time: ~6.1 seconds (5-7 seconds range)
- Retract time: ~5.5 seconds (4-6 seconds range)  
- Total cycle: ~11.5 seconds (extend + retract)
- Gap between cycles: ~5.1 seconds (operator positioning logs)
- Basket completion: 60 splits per basket
- Fuel consumption: Variable based on real farm data
"""

import asyncio
import json
import random
import time
import logging
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SplitterSimulator:
    """Simulates a firewood splitter controller with REAL FARM DATA timing patterns"""
    
    def __init__(self, broker_host="localhost", broker_port=1883, username=None, password=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client = None
        
        # REAL FARM DATA PARAMETERS (from production_data_corrupted.json analysis)
        self.avg_extend_time = 6.1      # 6.1 seconds average extend time
        self.extend_variation = 1.0      # ±1 second variation (5-7 seconds)
        self.avg_retract_time = 5.5     # 5.5 seconds average retract time  
        self.retract_variation = 1.0     # ±1 second variation (4-6 seconds)
        self.avg_gap_time = 5.1         # 5.1 seconds between cycles (log positioning)
        self.gap_variation = 3.0         # ±3 seconds variation (2-8 seconds)
        
        self.splits_per_basket = 60      # Real farm data: 60 splits per basket
        self.fuel_per_basket = 0.6       # Real farm average: ~0.6 gallons per basket
        self.abort_rate = 0.07           # Real farm data: ~7% abort rate
        
        # Current state
        self.current_sequence_stage = "IDLE"
        self.current_pressure = 0.0
        self.current_fuel_level = 5.0    # Start with 5 gallons (realistic farm level)
        self.splits_in_current_basket = 0
        self.basket_start_time = time.time()
        self.last_cycle_time = time.time()
        
        # Running totals
        self.total_splits = 0
        self.total_baskets = 0
        self.total_cycles = 0
        self.session_start_time = time.time()
        
        # Simulation control
        self.running = False
        self.simulation_speed = 1.0      # 1.0 = real time, 10.0 = 10x speed
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client()
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                logger.info(f"Using MQTT credentials for user: {self.username}")
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        logger.warning("Disconnected from MQTT broker")
    
    def publish_message(self, topic: str, payload: str):
        """Publish a message to MQTT topic"""
        if self.client:
            try:
                self.client.publish(topic, payload)
                logger.debug(f"Published to {topic}: {payload}")
            except Exception as e:
                logger.error(f"Failed to publish to {topic}: {e}")
    
    def get_realistic_extend_time(self) -> float:
        """Get realistic extend time based on farm data (5-7 seconds)"""
        return max(4.0, random.uniform(
            self.avg_extend_time - self.extend_variation,
            self.avg_extend_time + self.extend_variation
        ))
    
    def get_realistic_retract_time(self) -> float:
        """Get realistic retract time based on farm data (4-6 seconds)"""
        return max(3.0, random.uniform(
            self.avg_retract_time - self.retract_variation,
            self.avg_retract_time + self.retract_variation
        ))
    
    def get_realistic_gap_time(self) -> float:
        """Get realistic gap between cycles (2-8 seconds for log positioning)"""
        return max(1.0, random.uniform(
            self.avg_gap_time - self.gap_variation,
            self.avg_gap_time + self.gap_variation
        ))
    
    def get_pressure_for_stage(self, stage: str) -> float:
        """Get realistic pressure reading for current stage"""
        base_pressures = {
            "IDLE": 50 + random.uniform(-10, 10),
            "EXTENDING": 1800 + random.uniform(-200, 400),
            "RETRACTING": 1600 + random.uniform(-150, 300),
            "PRESSURE_RELIEF": 200 + random.uniform(-50, 100)
        }
        return max(0, base_pressures.get(stage, 50))
    
    def update_fuel_level(self):
        """Update fuel level based on usage"""
        # Consume fuel proportionally to splits completed
        fuel_per_split = self.fuel_per_basket / self.splits_per_basket
        self.current_fuel_level = max(0, self.current_fuel_level - fuel_per_split)
    
    async def simulate_production_cycle(self):
        """Simulate a single production cycle with REAL FARM DATA timing patterns"""
        
        # Check for random abort (7% chance based on real farm data)
        will_abort = random.random() < self.abort_rate
        cycle_id = self.total_cycles + 1
        
        logger.info(f"Starting production cycle #{cycle_id}")
        
        # Publish sequence start (LogSplitter Controller topics)
        self.publish_message("controller/sequence/active", "1")
        self.publish_message("controller/sequence/stage", "1")
        self.publish_message("controller/sequence/event", "started_R1")
        
        # EXTENDING phase with realistic timing
        self.current_sequence_stage = "EXTENDING"
        extend_start_time = time.time()
        extend_duration = self.get_realistic_extend_time() / self.simulation_speed
        
        # Activate extend relay
        self.publish_message("controller/relays/1/state", "1")  # Extend valve ON
        
        # Simulate extend phase with pressure updates
        elapsed = 0.0
        while elapsed < extend_duration:
            self.current_pressure = self.get_pressure_for_stage("EXTENDING")
            self.publish_message("controller/pressure/hydraulic_system", f"{self.current_pressure:.1f}")
            
            sleep_time = min(0.5 / self.simulation_speed, extend_duration - elapsed)
            await asyncio.sleep(sleep_time)
            elapsed += sleep_time
        
        # Extend limit reached
        self.publish_message("controller/inputs/6/state", "1")  # Extend limit switch
        self.publish_message("controller/relays/1/state", "0")  # Extend valve OFF
        
        extend_complete_time = time.time()
        
        # Check for abort during extend
        if will_abort and random.random() < 0.5:  # 50% chance abort happens during extend
            await self.simulate_cycle_abort("extend", extend_start_time, extend_complete_time, None, None)
            return
        
        # Switch to retract sequence
        self.publish_message("controller/sequence/event", "switched_to_R2_pressure_or_limit")
        self.publish_message("controller/sequence/stage", "2")
        self.publish_message("controller/inputs/6/state", "0")  # Extend limit released
        
        # RETRACTING phase with realistic timing  
        self.current_sequence_stage = "RETRACTING"
        retract_start_time = time.time()
        retract_duration = self.get_realistic_retract_time() / self.simulation_speed
        
        # Activate retract relay
        self.publish_message("controller/relays/2/state", "1")  # Retract valve ON
        
        # Simulate retract phase with pressure updates
        elapsed = 0.0
        while elapsed < retract_duration:
            self.current_pressure = self.get_pressure_for_stage("RETRACTING")
            self.publish_message("controller/pressure/hydraulic_system", f"{self.current_pressure:.1f}")
            
            sleep_time = min(0.5 / self.simulation_speed, retract_duration - elapsed)
            await asyncio.sleep(sleep_time)
            elapsed += sleep_time
        
        # Retract limit reached
        self.publish_message("controller/inputs/7/state", "1")  # Retract limit switch
        self.publish_message("controller/relays/2/state", "0")  # Retract valve OFF
        
        retract_complete_time = time.time()
        
        # Check for abort during retract
        if will_abort:  # Remaining aborts happen during retract
            await self.simulate_cycle_abort("retract", extend_start_time, extend_complete_time, 
                                          retract_start_time, retract_complete_time)
            return
        
        # SUCCESSFUL CYCLE COMPLETION
        self.current_sequence_stage = "IDLE"
        complete_time = time.time()
        
        # Sequence complete
        self.publish_message("controller/sequence/event", "complete_pressure_or_limit")
        self.publish_message("controller/sequence/active", "0")  # Sequence inactive
        self.publish_message("controller/sequence/stage", "0")   # Stage 0 = idle
        self.publish_message("controller/inputs/7/state", "0")   # Retract limit released
        
        # Update counters
        self.total_cycles += 1
        self.total_splits += 1
        self.splits_in_current_basket += 1
        self.last_cycle_time = time.time()
        self.update_fuel_level()
        
        # Publish fuel level
        self.publish_message("monitor/fuel/gallons", f"{self.current_fuel_level:.2f}")
        
        # Publish idle pressure
        self.current_pressure = self.get_pressure_for_stage("IDLE")
        self.publish_message("controller/pressure/hydraulic_system", f"{self.current_pressure:.1f}")
        
        logger.info(f"Completed split #{self.total_splits} "
                   f"({self.splits_in_current_basket}/{self.splits_per_basket} in current basket)")
    
    async def simulate_cycle_abort(self, abort_stage, extend_start, extend_complete, retract_start, retract_complete):
        """Simulate a cycle abort based on real farm patterns"""
        cycle_id = self.total_cycles + 1
        complete_time = time.time()
        
        logger.warning(f"Cycle #{cycle_id} ABORTED during {abort_stage}")
        
        # Publish abort sequence events
        self.publish_message("controller/sequence/event", "abort")
        self.publish_message("controller/relays/1/state", "0")  # All valves OFF
        self.publish_message("controller/relays/2/state", "0")
        self.publish_message("controller/sequence/active", "0")  # Sequence inactive
        self.publish_message("controller/sequence/stage", "0")   # Return to idle
        
        # Return to idle
        self.current_sequence_stage = "IDLE"
        self.total_cycles += 1  # Count the attempt
        # Note: Don't increment total_splits or splits_in_current_basket for aborts
    
    async def check_basket_completion(self):
        """Check if current basket should be completed"""
        basket_duration = time.time() - self.basket_start_time
        basket_duration_minutes = basket_duration / 60
        
        # Complete basket if we've reached target splits or time limit
        should_complete = (
            self.splits_in_current_basket >= self.splits_per_basket or
            basket_duration_minutes >= 35  # Maximum 35 minutes per basket
        )
        
        if should_complete:
            await self.complete_basket()
    
    async def complete_basket(self):
        """Complete the current basket and start a new one"""
        basket_duration = time.time() - self.basket_start_time
        basket_duration_minutes = basket_duration / 60
        
        self.total_baskets += 1
        
        logger.info(f"🗑️ BASKET COMPLETE #{self.total_baskets}: "
                   f"{self.splits_in_current_basket} splits in {basket_duration_minutes:.1f} minutes")
        
        # Simulate operator input for basket exchange (LogSplitter Controller topic)
        self.publish_message("controller/inputs/3/state", "1")  # Basket exchange signal
        self.publish_message("controller/control/resp", f"basket_{self.total_baskets}_complete")
        await asyncio.sleep(0.2 / self.simulation_speed)
        self.publish_message("controller/inputs/3/state", "0")
        
        # Reset for new basket
        self.splits_in_current_basket = 0
        self.basket_start_time = time.time()
        
        # Simulate brief pause for basket exchange (5-15 seconds)
        exchange_pause = random.uniform(5, 15) / self.simulation_speed
        logger.info(f"Pausing {exchange_pause:.1f}s for basket exchange...")
        await asyncio.sleep(exchange_pause)
    
    async def simulate_occasional_events(self):
        """Simulate occasional events like safety stops, aborts, etc."""
        # Small chance of safety or abort events
        if random.random() < 0.02:  # 2% chance per cycle
            event_type = random.choice(["safety", "abort", "estop"])
            
            if event_type == "safety":
                logger.warning("Simulating safety system activation")
                self.publish_message("controller/safety/active", "1")
                await asyncio.sleep(0.5 / self.simulation_speed)
                self.publish_message("controller/safety/active", "0")
                
            elif event_type == "abort":
                logger.warning("Simulating sequence abort")
                self.publish_message("controller/sequence/event", "abort")
                self.publish_message("controller/sequence/state", "abort")
                
            elif event_type == "estop":
                logger.warning("Simulating emergency stop")
                self.publish_message("controller/safety/estop", "1")
                await asyncio.sleep(1.0 / self.simulation_speed)
                self.publish_message("controller/safety/estop", "0")
                
            # Return to idle after event
            await asyncio.sleep(1.0 / self.simulation_speed)
            self.current_sequence_stage = "IDLE"
            self.publish_message("r4/sequence/status", "IDLE")
    
    async def publish_periodic_data(self):
        """Publish periodic data updates using LogSplitter Controller topics"""
        while self.running:
            try:
                # Publish current pressure
                self.current_pressure = self.get_pressure_for_stage(self.current_sequence_stage)
                self.publish_message("controller/pressure/hydraulic_system", f"{self.current_pressure:.1f}")
                
                # Publish hydraulic filter pressure (much lower)
                filter_pressure = random.uniform(10, 25)
                self.publish_message("controller/pressure/hydraulic_filter", f"{filter_pressure:.1f}")
                
                # Publish fuel level
                self.publish_message("monitor/fuel/gallons", f"{self.current_fuel_level:.2f}")
                
                await asyncio.sleep(10.0 / self.simulation_speed)  # Every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic data publishing: {e}")
                await asyncio.sleep(1.0)
    
    async def run_simulation(self, duration_minutes: Optional[float] = None):
        """Run the production simulation"""
        logger.info("🪓 Starting Firewood Splitter Simulation")
        logger.info(f"Parameters: {self.avg_cycle_time}s avg cycle, "
                   f"{self.splits_per_basket} splits/basket, "
                   f"{self.fuel_per_basket} gal/basket")
        logger.info(f"Simulation speed: {self.simulation_speed}x")
        
        if not self.connect_mqtt():
            return
        
        self.running = True
        self.session_start_time = time.time()
        self.basket_start_time = time.time()
        
        # Start periodic data publishing
        periodic_task = asyncio.create_task(self.publish_periodic_data())
        
        try:
            end_time = None
            if duration_minutes:
                end_time = time.time() + (duration_minutes * 60 / self.simulation_speed)
            
            while self.running:
                # Check if simulation should end
                if end_time and time.time() >= end_time:
                    logger.info("Simulation duration completed")
                    break
                
                # Wait for realistic gap time between cycles (log positioning)
                gap_time = self.get_realistic_gap_time() / self.simulation_speed
                await asyncio.sleep(gap_time)
                
                # Check if we have fuel
                if self.current_fuel_level <= 0:
                    logger.warning("⛽ Out of fuel! Simulation stopped.")
                    break
                
                # Run a production cycle
                await self.simulate_production_cycle()
                
                # Simulate occasional events
                await self.simulate_occasional_events()
                
                # Check if basket should be completed
                await self.check_basket_completion()
                
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            self.running = False
            periodic_task.cancel()
            
            # Final statistics
            session_duration = time.time() - self.session_start_time
            session_hours = session_duration / 3600
            
            logger.info("📊 SIMULATION COMPLETE")
            logger.info(f"Session Duration: {session_hours:.2f} hours")
            logger.info(f"Total Baskets: {self.total_baskets}")
            logger.info(f"Total Splits: {self.total_splits}")
            logger.info(f"Fuel Remaining: {self.current_fuel_level:.2f} gallons")
            
            if session_hours > 0:
                logger.info(f"Production Rate: {self.total_splits / session_hours:.1f} splits/hour")
                logger.info(f"Basket Rate: {self.total_baskets / session_hours:.1f} baskets/hour")
            
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()

async def main():
    """Main function to run the simulator"""
    import argparse
    from config import Config
    
    parser = argparse.ArgumentParser(description="Firewood Splitter Simulator")
    parser.add_argument("--host", help="MQTT broker host (overrides config)")
    parser.add_argument("--port", type=int, help="MQTT broker port (overrides config)")
    parser.add_argument("--username", help="MQTT username (overrides config)")
    parser.add_argument("--password", help="MQTT password (overrides config)")
    parser.add_argument("--duration", type=float, help="Simulation duration in minutes")
    parser.add_argument("--speed", type=float, default=1.0, help="Simulation speed multiplier")
    parser.add_argument("--splits-per-basket", type=int, default=60, help="Splits per basket")
    parser.add_argument("--cycle-time", type=float, default=30.0, help="Average cycle time in seconds")
    
    args = parser.parse_args()
    
    # Load config for MQTT settings
    config = Config()
    
    # Use command line args or config values
    host = args.host or config.mqtt_host
    port = args.port or config.mqtt_port
    username = args.username or config.mqtt_username
    password = args.password or config.mqtt_password
    
    simulator = SplitterSimulator(host, port, username, password)
    simulator.simulation_speed = args.speed
    simulator.splits_per_basket = args.splits_per_basket
    simulator.avg_cycle_time = args.cycle_time
    
    await simulator.run_simulation(args.duration)

if __name__ == "__main__":
    asyncio.run(main())