import time
import threading
from typing import Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TopicStats:
    """Statistics for a single MQTT topic"""
    
    def __init__(self, topic: str):
        self.topic = topic
        self.count = 0
        self.total = 0.0
        self.min_value = float('inf')
        self.max_value = float('-inf')
        self.last_value = None
        self.last_updated = None
        self.start_time = time.time()
        
    def add_value(self, value: float):
        """Add a new value and update statistics"""
        self.count += 1
        self.total += value
        self.last_value = value
        self.last_updated = time.time()
        
        # Update min/max
        if value < self.min_value:
            self.min_value = value
        if value > self.max_value:
            self.max_value = value
    
    @property
    def average(self) -> float:
        """Calculate running average"""
        return self.total / self.count if self.count > 0 else 0.0
    
    @property
    def rate_per_minute(self) -> float:
        """Calculate message rate per minute"""
        elapsed = time.time() - self.start_time
        return (self.count * 60) / elapsed if elapsed > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary for JSON serialization"""
        return {
            'topic': self.topic,
            'count': self.count,
            'total': self.total,
            'average': self.average,
            'min': self.min_value if self.min_value != float('inf') else None,
            'max': self.max_value if self.max_value != float('-inf') else None,
            'last_value': self.last_value,
            'last_updated': self.last_updated,
            'rate_per_minute': self.rate_per_minute,
            'uptime_seconds': time.time() - self.start_time
        }

class StatsEngine:
    """Main statistics engine for processing MQTT data"""
    
    def __init__(self):
        self.topic_stats: Dict[str, TopicStats] = {}
        self.lock = threading.RLock()  # Thread-safe access
        self.start_time = time.time()
        
    def add_value(self, topic: str, value: float):
        """Add a value for a specific topic"""
        with self.lock:
            if topic not in self.topic_stats:
                logger.info(f"Creating new statistics tracker for topic: {topic}")
                self.topic_stats[topic] = TopicStats(topic)
            
            self.topic_stats[topic].add_value(value)
            logger.debug(f"Added value {value} to topic {topic}")
    
    def get_topic_stats(self, topic: str) -> Dict[str, Any]:
        """Get statistics for a specific topic"""
        with self.lock:
            if topic in self.topic_stats:
                return self.topic_stats[topic].to_dict()
            return None
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all topics"""
        with self.lock:
            stats = {}
            for topic, topic_stat in self.topic_stats.items():
                stats[topic] = topic_stat.to_dict()
            
            # Add global statistics
            total_messages = sum(stat.count for stat in self.topic_stats.values())
            global_stats = {
                'total_topics': len(self.topic_stats),
                'total_messages': total_messages,
                'uptime_seconds': time.time() - self.start_time,
                'topics': stats
            }
            
            return global_stats
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key statistics"""
        with self.lock:
            if not self.topic_stats:
                return {
                    'total_topics': 0,
                    'total_messages': 0,
                    'uptime_seconds': time.time() - self.start_time,
                    'active_topics': []
                }
            
            total_messages = sum(stat.count for stat in self.topic_stats.values())
            active_topics = [
                {
                    'topic': topic,
                    'count': stat.count,
                    'average': stat.average,
                    'last_value': stat.last_value,
                    'rate_per_minute': stat.rate_per_minute
                }
                for topic, stat in self.topic_stats.items()
            ]
            
            # Sort by message count descending
            active_topics.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'total_topics': len(self.topic_stats),
                'total_messages': total_messages,
                'uptime_seconds': time.time() - self.start_time,
                'active_topics': active_topics
            }
    
    def reset_stats(self):
        """Reset all statistics"""
        with self.lock:
            logger.info("Resetting all statistics")
            self.topic_stats.clear()
            self.start_time = time.time()