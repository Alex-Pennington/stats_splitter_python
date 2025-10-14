#!/usr/bin/env python3
"""
Test MQTT stats API endpoint
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_server import create_app
from production_stats import ProductionStatsEngine
from stats_engine import StatsEngine

def test_mqtt_stats_api():
    """Test MQTT stats API"""
    print("Testing MQTT stats API...")
    
    # Create test app with stats engine
    production_stats = ProductionStatsEngine()
    app = create_app(production_stats)
    
    # Create and attach a stats engine with test data
    mqtt_stats_engine = StatsEngine()
    
    # Add some test MQTT data
    mqtt_stats_engine.add_value('monitor/temperature/local', 72.5)
    mqtt_stats_engine.add_value('monitor/temperature/local', 73.1)
    mqtt_stats_engine.add_value('monitor/fuel/gallons', 12.3)
    mqtt_stats_engine.add_value('controller/pressure/hydraulic_system', 2500.0)
    mqtt_stats_engine.add_value('controller/sequence/event', 1.0)  # Non-numeric treated as count
    
    app.mqtt_stats_engine = mqtt_stats_engine
    
    # Test the API endpoint
    with app.test_client() as client:
        try:
            response = client.get('/api/mqtt/stats')
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ MQTT Stats API working!")
                print(f"   Topics: {data.get('total_topics', 0)}")
                print(f"   Messages: {data.get('total_messages', 0)}")
                print(f"   Example topics:")
                for topic_name, topic_data in list(data.get('topics', {}).items())[:3]:
                    last_seen = "Has timestamp" if topic_data.get('last_timestamp') else "No timestamp"
                    print(f"     {topic_name}: {topic_data.get('count', 0)} msgs, {last_seen}")
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    test_mqtt_stats_api()