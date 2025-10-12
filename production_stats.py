import time
import threading
from typing import Dict, Any, List, Optional
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SequenceEvent(Enum):
    """Sequence events from r4/sequence/event"""
    START = "start"
    EXTEND_COMPLETE = "extend_complete"
    RETRACT_COMPLETE = "retract_complete"
    ABORT = "abort"
    TIMEOUT = "timeout"
    SAFETY_STOP = "safety_stop"

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
    
    def __init__(self):
        self.lock = threading.RLock()
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
        
        # Initialize first basket
        self._start_new_basket()
        
    def _start_new_basket(self):
        """Start a new basket session"""
        if self.current_basket and not self.current_basket.is_complete:
            # Complete the previous basket
            self.current_basket.complete_basket()
            self.completed_baskets.append(self.current_basket)
            
        self.current_basket = BasketSession()
        logger.info("Started new basket session")
        
    def handle_sequence_event(self, event: str, timestamp: float = None):
        """Process sequence events from r4/sequence/event"""
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
                
            if seq_event == SequenceEvent.START:
                # Start a new production cycle
                cycle = self.current_basket.start_new_cycle()
                cycle.start_extend()
                self.total_cycles += 1
                logger.info(f"Started new production cycle #{self.total_cycles}")
                
            elif seq_event == SequenceEvent.EXTEND_COMPLETE:
                if self.current_basket.current_cycle:
                    self.current_basket.current_cycle.complete_extend()
                    self.current_basket.current_cycle.start_retract()
                    
            elif seq_event == SequenceEvent.RETRACT_COMPLETE:
                if self.current_basket.current_cycle:
                    self.current_basket.current_cycle.complete_retract()
                    self.total_splits += 1
                    logger.info(f"Completed split #{self.total_splits}")
                    
            elif seq_event in [SequenceEvent.ABORT, SequenceEvent.TIMEOUT, SequenceEvent.SAFETY_STOP]:
                if self.current_basket.current_cycle:
                    self.current_basket.current_cycle.abort_cycle(event)
                    logger.warning(f"Cycle aborted: {event}")
    
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
                self.current_basket.complete_basket()
                self.completed_baskets.append(self.current_basket)
                self.total_baskets += 1
                
                splits_in_basket = self.current_basket.split_count
                basket_duration = self.current_basket.total_duration
                
                logger.info(f"Completed basket #{self.total_baskets}: "
                          f"{splits_in_basket} splits in {basket_duration:.1f}s")
                
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
            
            # Keep only last 100 readings
            if len(self.fuel_level_readings) > 100:
                self.fuel_level_readings = self.fuel_level_readings[-100:]
    
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
            
            # Calculate cycle time statistics
            completed_cycles = [
                cycle for basket in self.completed_baskets 
                for cycle in basket.cycles 
                if cycle.is_complete and not cycle.aborted
            ]
            
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
                'aborted_cycles': self.total_cycles - len(completed_cycles),
                'current_stage': self.current_sequence_stage.value,
                'system_status': 'active' if idle_time < 300 else 'idle'  # 5 minute idle threshold
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