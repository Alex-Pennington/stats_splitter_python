#!/usr/bin/env python3
"""
Simple test to verify web server routes and templates
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_server import create_app
from production_stats import ProductionStatsEngine

def test_routes():
    """Test all web routes are accessible"""
    print("Testing web server routes...")
    
    # Create test app
    production_stats = ProductionStatsEngine()
    app = create_app(production_stats)
    
    # Test routes
    routes_to_test = [
        ('/', 'Production Dashboard'),
        ('/baskets', 'Basket History'),
        ('/viewer', 'Data Viewer'),
        ('/stats', 'MQTT Stats Dashboard'),
        ('/monitor', 'Monitor Control Panel'),
        ('/health', 'Health Check'),
    ]
    
    with app.test_client() as client:
        for route, description in routes_to_test:
            try:
                response = client.get(route)
                status = "✅ OK" if response.status_code == 200 else f"❌ ERROR ({response.status_code})"
                print(f"{status} - {route:<12} - {description}")
            except Exception as e:
                print(f"❌ ERROR - {route:<12} - {description} - {str(e)}")
    
    print("\nAll routes tested!")

if __name__ == "__main__":
    test_routes()