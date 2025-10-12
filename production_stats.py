import time
import threading
import json
import os
from typing import Dict, Any, List, Optional
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SequenceEvent(Enum):
    """Sequence events from LogSplitter Controller"""
    # Cycle control events
    CYCLE_START = "cycle_start"
    EXTEND_START = "extend_start"
    EXTEND_COMPLETE = "extend_complete"
    RETRACT_START = "retract_start"
    RETRACT_COMPLETE = "retract_complete"
    CYCLE_COMPLETE = "cycle_complete"
    
    # Sequence management
    SEQUENCE_START = "sequence_start"
    SEQUENCE_END = "sequence_end"
    
    # Safety and control events
    ABORT = "abort"
    TIMEOUT = "timeout"
    SAFETY_STOP = "safety_stop"
    EMERGENCY_STOP = "emergency_stop"
    SAFETY_CLEAR = "safety_clear"
    
    # Valve and limit events
    EXTEND_VALVE_ON = "extend_valve_on"
    RETRACT_VALVE_ON = "retract_valve_on"
    EXTEND_LIMIT_REACHED = "extend_limit_reached"
    RETRACT_LIMIT_REACHED = "retract_limit_reached"
    
    # Legacy events for backward compatibility
    START = "start"

class SequenceStage(Enum):
    """Sequence stages from r4/sequence/status"""
    IDLE = "IDLE"
    EXTENDING = "EXTENDING"
    RETRACTING = "RETRACTING"
    PRESSURE_RELIEF = "PRESSURE_RELIEF"

class ProductionCycle:
    """Represents a single extend/retract production cycle"""
    
    def __init__(self):
        self.start_time = time.time()
        self.extend_start = None
        self.extend_complete = None
        self.retract_start = None
        self.retract_complete = None
        self.complete_time = None
        self.aborted = False
        self.abort_reason = None
        
    def start_extend(self):
        """Mark the start of extend stage"""
        self.extend_start = time.time()
        
    def complete_extend(self):
        """Mark the completion of extend stage"""
        self.extend_complete = time.time()
        
    def start_retract(self):
        """Mark the start of retract stage"""
        self.retract_start = time.time()
        
    def complete_retract(self):
        """Mark the completion of retract stage (cycle complete)"""
        self.retract_complete = time.time()
        self.complete_time = time.time()
        
    def abort_cycle(self, reason: str):
        """Mark the cycle as aborted"""
        self.aborted = True
        self.abort_reason = reason
        self.complete_time = time.time()
        
    @property
    def is_complete(self) -> bool:
        """Check if the cycle is complete"""
        return self.complete_time is not None
        
    @property
    def total_duration(self) -> float:
        """Total cycle time in seconds"""
        if self.complete_time:
            return self.complete_time - self.start_time
        return time.time() - self.start_time
        
    @property
    def extend_duration(self) -> Optional[float]:
        """Extend stage duration in seconds"""
        if self.extend_start and self.extend_complete:
            return self.extend_complete - self.extend_start
        return None
        
    @property
    def retract_duration(self) -> Optional[float]:
        """Retract stage duration in seconds"""
        if self.retract_start and self.retract_complete:
            return self.retract_complete - self.retract_start
        return None

class BasketSession:
    """Represents a complete basket filling session"""
    
    def __init__(self):
        self.start_time = time.time()
        self.cycles: List[ProductionCycle] = []
        self.current_cycle: Optional[ProductionCycle] = None
        self.complete_time = None
        self.exchange_time = None
        self.start_fuel_level = None  # Fuel level at basket start
        self.end_fuel_level = None    # Fuel level at basket completion
        self.fuel_consumed = 0.0      # Calculated fuel consumption
        
    def start_new_cycle(self) -> ProductionCycle:
        """Start a new production cycle"""
        if self.current_cycle and not self.current_cycle.is_complete:
            # Complete the previous cycle as aborted
            self.current_cycle.abort_cycle("new_cycle_started")
            
        self.current_cycle = ProductionCycle()
        self.cycles.append(self.current_cycle)
        return self.current_cycle
        
    def complete_basket(self):
        """Mark the basket as complete (exchange signal received)"""
        self.complete_time = time.time()
        self.exchange_time = time.time()
        
        # If there's an active cycle, complete it
        if self.current_cycle and not self.current_cycle.is_complete:
            self.current_cycle.complete_retract()
            
    @property
    def is_complete(self) -> bool:
        """Check if the basket session is complete"""
        return self.complete_time is not None
        
    @property
    def total_duration(self) -> float:
        """Total basket session time in seconds"""
        if self.complete_time:
            return self.complete_time - self.start_time
        return time.time() - self.start_time
        
    @property
    def split_count(self) -> int:
        """Number of completed splits in this basket"""
        return len([c for c in self.cycles if c.is_complete and not c.aborted])
        
    @property
    def cycle_count(self) -> int:
        """Total number of cycles (including aborted)"""
        return len(self.cycles)

class ProductionStatsEngine:
    """Enhanced statistics engine for firewood splitter production analytics"""
    
    def __init__(self, data_file='production_data.json'):
        self.lock = threading.RLock()
        self.data_file = data_file
        self.start_time = time.time()
        
        # Current production state
        self.current_basket: Optional[BasketSession] = None
        self.current_sequence_stage = SequenceStage.IDLE
        
        # Historical data
        self.completed_baskets: List[BasketSession] = []
        self.daily_stats = defaultdict(dict)  # date -> stats
        
        # Real-time tracking
        self.total_cycles = 0
        self.total_splits = 0
        self.total_baskets = 0
        self.last_activity_time = time.time()
        
        # Performance metrics
        self.pressure_readings = []
        self.fuel_level_readings = []
        
        # Load existing data if available
        self._load_data()
        
        # Initialize first basket if none exists
        if not self.current_basket:
            self._start_new_basket()
        
    def _save_data(self):
        """Save production data to JSON file"""
        try:
            # Prepare data for serialization
            data = {
                'start_time': self.start_time,
                'total_cycles': self.total_cycles,
                'total_splits': self.total_splits,
                'total_baskets': self.total_baskets,
                'last_activity_time': self.last_activity_time,
                'completed_baskets': [],
                'current_basket': None,
                'current_sequence_stage': self.current_sequence_stage.value,
                'daily_stats': dict(self.daily_stats)
            }
            
            # Serialize completed baskets
            for basket in self.completed_baskets:
                basket_data = {
                    'start_time': basket.start_time,
                    'complete_time': basket.complete_time,
                    'exchange_time': basket.exchange_time,
                    'start_fuel_level': basket.start_fuel_level,
                    'end_fuel_level': basket.end_fuel_level,
                    'fuel_consumed': basket.fuel_consumed,
                    'cycles': []
                }
                
                # Serialize cycles in basket
                for cycle in basket.cycles:
                    cycle_data = {
                        'start_time': cycle.start_time,
                        'extend_start': cycle.extend_start,
                        'extend_complete': cycle.extend_complete,
                        'retract_start': cycle.retract_start,
                        'retract_complete': cycle.retract_complete,
                        'complete_time': cycle.complete_time,
                        'aborted': cycle.aborted,
                        'abort_reason': cycle.abort_reason
                    }
                    basket_data['cycles'].append(cycle_data)
                
                data['completed_baskets'].append(basket_data)
            
            # Serialize current basket if exists
            if self.current_basket:
                current_basket_data = {
                    'start_time': self.current_basket.start_time,
                    'complete_time': self.current_basket.complete_time,
                    'exchange_time': self.current_basket.exchange_time,
                    'start_fuel_level': self.current_basket.start_fuel_level,
                    'end_fuel_level': self.current_basket.end_fuel_level,
                    'fuel_consumed': self.current_basket.fuel_consumed,
                    'cycles': []
                }
                
                for cycle in self.current_basket.cycles:
                    cycle_data = {
                        'start_time': cycle.start_time,
                        'extend_start': cycle.extend_start,
                        'extend_complete': cycle.extend_complete,
                        'retract_start': cycle.retract_start,
                        'retract_complete': cycle.retract_complete,
                        'complete_time': cycle.complete_time,
                        'aborted': cycle.aborted,
                        'abort_reason': cycle.abort_reason
                    }
                    current_basket_data['cycles'].append(cycle_data)
                
                data['current_basket'] = current_basket_data
            
            # Save to file
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Production data saved to {self.data_file}")
            
        except Exception as e:
            logger.error(f"Failed to save production data: {e}")
    
    def _load_data(self):
        """Load production data from JSON file"""
        try:
            if not os.path.exists(self.data_file):
                logger.info("No existing production data file found, starting fresh")
                return
            
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Restore basic stats
            self.start_time = data.get('start_time', time.time())
            self.total_cycles = data.get('total_cycles', 0)
            self.total_splits = data.get('total_splits', 0)
            self.total_baskets = data.get('total_baskets', 0)
            self.last_activity_time = data.get('last_activity_time', time.time())
            self.daily_stats = defaultdict(dict, data.get('daily_stats', {}))
            
            # Restore sequence stage
            stage_value = data.get('current_sequence_stage', 'IDLE')
            try:
                self.current_sequence_stage = SequenceStage(stage_value)
            except ValueError:
                self.current_sequence_stage = SequenceStage.IDLE
            
            # Restore completed baskets
            self.completed_baskets = []
            for basket_data in data.get('completed_baskets', []):
                basket = BasketSession()
                basket.start_time = basket_data.get('start_time', time.time())
                basket.complete_time = basket_data.get('complete_time')
                basket.exchange_time = basket_data.get('exchange_time')
                basket.start_fuel_level = basket_data.get('start_fuel_level')
                basket.end_fuel_level = basket_data.get('end_fuel_level')
                basket.fuel_consumed = basket_data.get('fuel_consumed', 0.0)
                
                # Restore cycles in basket
                for cycle_data in basket_data.get('cycles', []):
                    cycle = ProductionCycle()
                    cycle.start_time = cycle_data.get('start_time', time.time())
                    cycle.extend_start = cycle_data.get('extend_start')
                    cycle.extend_complete = cycle_data.get('extend_complete')
                    cycle.retract_start = cycle_data.get('retract_start')
                    cycle.retract_complete = cycle_data.get('retract_complete')
                    cycle.complete_time = cycle_data.get('complete_time')
                    cycle.aborted = cycle_data.get('aborted', False)
                    cycle.abort_reason = cycle_data.get('abort_reason')
                    
                    basket.cycles.append(cycle)
                
                self.completed_baskets.append(basket)
            
            # Restore current basket
            current_basket_data = data.get('current_basket')
            if current_basket_data:
                self.current_basket = BasketSession()
                self.current_basket.start_time = current_basket_data.get('start_time', time.time())
                self.current_basket.complete_time = current_basket_data.get('complete_time')
                self.current_basket.exchange_time = current_basket_data.get('exchange_time')
                self.current_basket.start_fuel_level = current_basket_data.get('start_fuel_level')
                self.current_basket.end_fuel_level = current_basket_data.get('end_fuel_level')
                self.current_basket.fuel_consumed = current_basket_data.get('fuel_consumed', 0.0)
                
                # Restore cycles in current basket
                for cycle_data in current_basket_data.get('cycles', []):
                    cycle = ProductionCycle()
                    cycle.start_time = cycle_data.get('start_time', time.time())
                    cycle.extend_start = cycle_data.get('extend_start')
                    cycle.extend_complete = cycle_data.get('extend_complete')
                    cycle.retract_start = cycle_data.get('retract_start')
                    cycle.retract_complete = cycle_data.get('retract_complete')
                    cycle.complete_time = cycle_data.get('complete_time')
                    cycle.aborted = cycle_data.get('aborted', False)
                    cycle.abort_reason = cycle_data.get('abort_reason')
                    
                    self.current_basket.cycles.append(cycle)
                    
                    # Set current cycle if not complete
                    if not cycle.is_complete:
                        self.current_basket.current_cycle = cycle
            
            logger.info(f"Production data loaded: {self.total_splits} splits, {self.total_baskets} baskets, {self.total_cycles} cycles")
            
        except Exception as e:
            logger.error(f"Failed to load production data: {e}")
            logger.info("Starting with fresh production data")
        
    def _start_new_basket(self):
        """Start a new basket session"""
        if self.current_basket and not self.current_basket.is_complete:
            # Complete the previous basket
            self.current_basket.complete_basket()
            self.completed_baskets.append(self.current_basket)
            
        self.current_basket = BasketSession()
        logger.info("Started new basket session")
        
    def handle_sequence_event(self, event: str, timestamp: float = None):
        """Process sequence events from LogSplitter Controller"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            self.last_activity_time = timestamp
            
            try:
                seq_event = SequenceEvent(event.lower())
            except ValueError:
                logger.warning(f"Unknown sequence event: {event}")
                return
                
            if not self.current_basket:
                self._start_new_basket()
                
            # Handle cycle start events and update stage
            if seq_event in [SequenceEvent.START, SequenceEvent.CYCLE_START, SequenceEvent.EXTEND_START]:
                if not self.current_basket.current_cycle or self.current_basket.current_cycle.is_complete:
                    # Start a new production cycle
                    cycle = self.current_basket.start_new_cycle()
                    cycle.start_extend()
                    self.total_cycles += 1
                    self.current_sequence_stage = SequenceStage.EXTENDING
                    logger.info(f"Started new production cycle #{self.total_cycles} - Stage: EXTENDING")
                
            # Handle extend completion and update stage
            elif seq_event == SequenceEvent.EXTEND_COMPLETE:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    self.current_basket.current_cycle.complete_extend()
                    self.current_basket.current_cycle.start_retract()
                    self.current_sequence_stage = SequenceStage.RETRACTING
                    logger.info("Extend phase completed, starting retract - Stage: RETRACTING")
                    
            # Handle retract start and update stage
            elif seq_event == SequenceEvent.RETRACT_START:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    if not self.current_basket.current_cycle.retract_start:
                        self.current_basket.current_cycle.start_retract()
                    self.current_sequence_stage = SequenceStage.RETRACTING
                    logger.debug("Retract phase started")
                    
            # Handle cycle completion and return to idle
            elif seq_event in [SequenceEvent.RETRACT_COMPLETE, SequenceEvent.CYCLE_COMPLETE]:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    self.current_basket.current_cycle.complete_retract()
                    self.total_splits += 1
                    self.current_sequence_stage = SequenceStage.IDLE
                    logger.info(f"Completed split #{self.total_splits} - Stage: IDLE")
                    
                    # Save data after each split completion
                    self._save_data()
                    
                    # Check if basket is full (typically 60 splits)
                    if self.current_basket.split_count >= 60:
                        self.handle_basket_exchange()
                        
            # Handle limit switch activations
            elif seq_event == SequenceEvent.EXTEND_LIMIT_REACHED:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    if not self.current_basket.current_cycle.extend_complete:
                        self.current_basket.current_cycle.complete_extend()
                        self.current_sequence_stage = SequenceStage.RETRACTING
                        logger.debug("Extend limit reached")
                        
            elif seq_event == SequenceEvent.RETRACT_LIMIT_REACHED:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    self.current_basket.current_cycle.complete_retract()
                    self.total_splits += 1
                    self.current_sequence_stage = SequenceStage.IDLE
                    logger.info(f"Split completed by retract limit #{self.total_splits}")
                    
                    # Save data after each split completion
                    self._save_data()
                    
            # Handle safety events
            elif seq_event in [SequenceEvent.SAFETY_STOP, SequenceEvent.EMERGENCY_STOP]:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    self.current_basket.current_cycle.abort_cycle(event)
                    self.current_sequence_stage = SequenceStage.IDLE
                    logger.warning(f"Cycle aborted by safety system: {event}")
                    
            elif seq_event == SequenceEvent.SAFETY_CLEAR:
                logger.info("Safety system cleared, ready for operation")
                
            # Handle abort and timeout
            elif seq_event in [SequenceEvent.ABORT, SequenceEvent.TIMEOUT]:
                if self.current_basket.current_cycle and not self.current_basket.current_cycle.is_complete:
                    self.current_basket.current_cycle.abort_cycle(event)
                    self.current_sequence_stage = SequenceStage.IDLE
                    logger.warning(f"Cycle aborted: {event}")
                    
            # Handle valve operations (for diagnostics)
            elif seq_event in [SequenceEvent.EXTEND_VALVE_ON, SequenceEvent.RETRACT_VALVE_ON]:
                logger.debug(f"Hydraulic valve operation: {event}")
                
            # Handle sequence management
            elif seq_event == SequenceEvent.SEQUENCE_START:
                logger.info("Production sequence started")
                # Don't change stage here - let specific events handle it
                
            elif seq_event == SequenceEvent.SEQUENCE_END:
                self.current_sequence_stage = SequenceStage.IDLE
                logger.info("Production sequence ended")
    
    def handle_sequence_status(self, status: str, timestamp: float = None):
        """Process sequence status from r4/sequence/status"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            try:
                self.current_sequence_stage = SequenceStage(status.upper())
            except ValueError:
                logger.warning(f"Unknown sequence status: {status}")
    
    def handle_basket_exchange(self, timestamp: float = None):
        """Process basket exchange signal from controller/signals/basket_exchange"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            self.last_activity_time = timestamp
            
            if self.current_basket:
                # Calculate fuel consumption for this basket
                current_fuel = self._get_latest_fuel_level()
                if self.current_basket.start_fuel_level is not None and current_fuel is not None:
                    self.current_basket.end_fuel_level = current_fuel
                    self.current_basket.fuel_consumed = self.current_basket.start_fuel_level - current_fuel
                    if self.current_basket.fuel_consumed < 0:
                        self.current_basket.fuel_consumed = 0.0  # Handle fuel refill case
                
                self.current_basket.complete_basket()
                self.completed_baskets.append(self.current_basket)
                self.total_baskets += 1
                
                splits_in_basket = self.current_basket.split_count
                basket_duration = self.current_basket.total_duration
                fuel_consumed = self.current_basket.fuel_consumed
                
                logger.info(f"Completed basket #{self.total_baskets}: "
                          f"{splits_in_basket} splits in {basket_duration:.1f}s, "
                          f"fuel consumed: {fuel_consumed:.2f} gallons")
                
                # Save data after basket completion
                self._save_data()
                
                # Start new basket
                self._start_new_basket()
    
    def handle_pressure_reading(self, pressure: float, sensor_type: str = "hydraulic", timestamp: float = None):
        """Process pressure readings from r4/pressure/* topics"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            self.pressure_readings.append({
                'timestamp': timestamp,
                'pressure': pressure,
                'sensor': sensor_type
            })
            
            # Keep only last 1000 readings
            if len(self.pressure_readings) > 1000:
                self.pressure_readings = self.pressure_readings[-1000:]
    
    def handle_fuel_level(self, fuel_level: float, timestamp: float = None):
        """Process fuel level readings from monitor/fuel_level"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            self.fuel_level_readings.append({
                'timestamp': timestamp,
                'fuel_level': fuel_level
            })
            
            # If we have a current basket and no start fuel level, set it
            if self.current_basket and self.current_basket.start_fuel_level is None:
                self.current_basket.start_fuel_level = fuel_level
                logger.info(f"Set basket start fuel level: {fuel_level} gallons")
            
            # Keep only last 100 readings
            if len(self.fuel_level_readings) > 100:
                self.fuel_level_readings = self.fuel_level_readings[-100:]
    
    def _get_latest_fuel_level(self) -> Optional[float]:
        """Get the most recent fuel level reading"""
        if self.fuel_level_readings:
            return self.fuel_level_readings[-1]['fuel_level']
        return None
    
    def get_current_basket_stats(self) -> Dict[str, Any]:
        """Get statistics for the current basket"""
        with self.lock:
            if not self.current_basket:
                return {}
                
            return {
                'basket_duration': self.current_basket.total_duration,
                'splits_completed': self.current_basket.split_count,
                'cycles_attempted': self.current_basket.cycle_count,
                'current_stage': self.current_sequence_stage.value,
                'active_cycle_duration': (
                    self.current_basket.current_cycle.total_duration 
                    if self.current_basket.current_cycle else 0
                )
            }
    
    def get_production_rates(self) -> Dict[str, float]:
        """Calculate current production rates"""
        with self.lock:
            uptime_hours = (time.time() - self.start_time) / 3600
            
            # Calculate rates
            splits_per_hour = self.total_splits / uptime_hours if uptime_hours > 0 else 0
            baskets_per_hour = self.total_baskets / uptime_hours if uptime_hours > 0 else 0
            
            # Current basket rate
            current_basket_rate = 0
            if self.current_basket and self.current_basket.total_duration > 0:
                current_basket_rate = (self.current_basket.split_count * 3600) / self.current_basket.total_duration
            
            return {
                'splits_per_hour': splits_per_hour,
                'baskets_per_hour': baskets_per_hour,
                'current_basket_splits_per_hour': current_basket_rate,
                'average_splits_per_basket': (
                    self.total_splits / self.total_baskets if self.total_baskets > 0 else 0
                )
            }
    
    def get_production_summary(self) -> Dict[str, Any]:
        """Get comprehensive production summary"""
        with self.lock:
            uptime_seconds = time.time() - self.start_time
            idle_time = time.time() - self.last_activity_time
            
            # Calculate cycle time statistics from all baskets (completed + current)
            all_cycles = []
            
            # Add cycles from completed baskets
            for basket in self.completed_baskets:
                all_cycles.extend(basket.cycles)
            
            # Add cycles from current basket
            if self.current_basket:
                all_cycles.extend(self.current_basket.cycles)
            
            # Count completed vs aborted cycles
            completed_cycles = [cycle for cycle in all_cycles if cycle.is_complete and not cycle.aborted]
            aborted_cycles = [cycle for cycle in all_cycles if cycle.aborted]
            
            avg_cycle_time = 0
            if completed_cycles:
                avg_cycle_time = sum(c.total_duration for c in completed_cycles) / len(completed_cycles)
            
            return {
                'uptime_seconds': uptime_seconds,
                'idle_time_seconds': idle_time,
                'total_baskets': self.total_baskets,
                'total_splits': self.total_splits,
                'total_cycles': self.total_cycles,
                'current_basket': self.get_current_basket_stats(),
                'production_rates': self.get_production_rates(),
                'average_cycle_time': avg_cycle_time,
                'completed_cycles': len(completed_cycles),
                'aborted_cycles': len(aborted_cycles),
                'current_stage': self.current_sequence_stage.value,
                'system_status': 'active' if idle_time < 300 else 'idle'  # 5 minute idle threshold
            }
    
    def get_basket_history(self) -> Dict[str, Any]:
        """Get detailed history of all completed baskets"""
        with self.lock:
            baskets = []
            
            for i, basket in enumerate(self.completed_baskets):
                basket_data = {
                    'basket_number': i + 1,
                    'start_time': basket.start_time,
                    'start_time_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(basket.start_time)),
                    'complete_time': basket.complete_time,
                    'complete_time_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(basket.complete_time)) if basket.complete_time else None,
                    'duration_seconds': basket.total_duration,
                    'duration_formatted': f"{basket.total_duration:.1f}s" if basket.total_duration > 0 else "0s",
                    'splits_completed': basket.split_count,
                    'cycles_attempted': basket.cycle_count,
                    'success_rate': (basket.split_count / basket.cycle_count * 100) if basket.cycle_count > 0 else 0,
                    'start_fuel_level': basket.start_fuel_level,
                    'end_fuel_level': basket.end_fuel_level,
                    'fuel_consumed': basket.fuel_consumed,
                    'splits_per_gallon': (basket.split_count / basket.fuel_consumed) if basket.fuel_consumed > 0 else 0
                }
                baskets.append(basket_data)
            
            # Include current basket if exists
            current_basket_data = None
            if self.current_basket:
                current_fuel = self._get_latest_fuel_level()
                fuel_consumed_current = 0.0
                if self.current_basket.start_fuel_level is not None and current_fuel is not None:
                    fuel_consumed_current = max(0.0, self.current_basket.start_fuel_level - current_fuel)
                
                current_basket_data = {
                    'basket_number': len(self.completed_baskets) + 1,
                    'start_time': self.current_basket.start_time,
                    'start_time_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.current_basket.start_time)),
                    'complete_time': None,
                    'complete_time_formatted': 'In Progress',
                    'duration_seconds': self.current_basket.total_duration,
                    'duration_formatted': f"{self.current_basket.total_duration:.1f}s",
                    'splits_completed': self.current_basket.split_count,
                    'cycles_attempted': self.current_basket.cycle_count,
                    'success_rate': (self.current_basket.split_count / self.current_basket.cycle_count * 100) if self.current_basket.cycle_count > 0 else 0,
                    'start_fuel_level': self.current_basket.start_fuel_level,
                    'end_fuel_level': current_fuel,
                    'fuel_consumed': fuel_consumed_current,
                    'splits_per_gallon': (self.current_basket.split_count / fuel_consumed_current) if fuel_consumed_current > 0 else 0
                }
            
            return {
                'completed_baskets': baskets,
                'current_basket': current_basket_data,
                'total_baskets_completed': len(self.completed_baskets),
                'total_fuel_consumed': sum(basket.fuel_consumed for basket in self.completed_baskets),
                'average_fuel_per_basket': sum(basket.fuel_consumed for basket in self.completed_baskets) / len(self.completed_baskets) if self.completed_baskets else 0
            }
    
    def reset_stats(self):
        """Reset all production statistics"""
        with self.lock:
            logger.info("Resetting production statistics")
            self.completed_baskets.clear()
            self.daily_stats.clear()
            self.pressure_readings.clear()
            self.fuel_level_readings.clear()
            
            self.total_cycles = 0
            self.total_splits = 0
            self.total_baskets = 0
            self.start_time = time.time()
            self.last_activity_time = time.time()
            
            self.current_basket = None
            self.current_sequence_stage = SequenceStage.IDLE
            self._start_new_basket()
            
            # Save the reset state
            self._save_data()