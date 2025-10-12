# Copilot Instructions for stats_splitter_python

## Project Overview
This is a specialized Python application for **firewood splitter production monitoring**. It subscribes to MQTT topics from industrial firewood splitter controllers, calculates real-time production statistics (cycles, baskets, rates), and serves a web dashboard for live monitoring. The system processes data from hydraulic log splitters with embedded IoT controllers.

## Architecture & Key Components
- **MQTT Production Monitor**: Connects to firewood splitter controller MQTT topics for real-time data
- **Production Statistics Engine**: Specialized analytics for splitting cycles, basket completion, and production rates
- **Windows-Compatible Implementation**: Uses synchronous MQTT client for Windows asyncio compatibility
- **Live Production Dashboard**: Flask web server with real-time production metrics and REST APIs
- **Production Simulator**: MQTT publisher that simulates realistic firewood splitter operations

## Industrial Context
This system monitors **commercial firewood splitter operations** with these key metrics:
- **Production Cycles**: Individual log splitting operations (30-second average cycle time)
- **Basket Sessions**: Collections of 60 splits per basket (30-minute sessions)
- **Production Rates**: Splits per hour, baskets per hour, efficiency tracking
- **Resource Monitoring**: Fuel consumption, maintenance intervals, operational status

## Development Workflow
```powershell
# Install dependencies
pip install -r requirements.txt

# Run main application (Windows-compatible)
python main_windows.py

# Run production simulator (for testing)
python simulator.py --duration 10 --speed 2

# Test with real MQTT broker
python main_windows.py  # Uses credentials from .env

# Run unit tests
python -m pytest tests/

# Test API endpoints
# Visit http://localhost:5000 for dashboard
# Visit http://localhost:5000/api/production/summary for API
```

## MQTT Topic Architecture
The system subscribes to 6 production-specific topics from firewood splitter controllers:
- `firewood/splitter/001/cycle_start` - Production cycle initiation
- `firewood/splitter/001/split_complete` - Individual split completion
- `firewood/splitter/001/basket_status` - Basket fill status updates
- `firewood/splitter/001/engine_stats` - Engine performance metrics
- `firewood/splitter/001/hydraulic_pressure` - Hydraulic system data
- `firewood/splitter/001/maintenance_alert` - Service and maintenance notifications

## Key Conventions
- **Production-First Design**: All components optimized for industrial firewood production monitoring
- **Windows Compatibility**: Use `main_windows.py` with synchronous MQTT for Windows deployment
- **Real-Time Processing**: Thread-safe statistics with immediate dashboard updates
- **MQTT Message Patterns**: JSON payloads with production cycle IDs, timestamps, and metrics
- **Configuration Management**: `.env` files for MQTT broker credentials and production parameters
- **Industrial Logging**: Comprehensive logging for production troubleshooting and auditing

## Critical Files & Modules
- **`main_windows.py`**: Windows-compatible application entry point with synchronous MQTT client
- **`production_stats.py`**: Core production analytics engine with ProductionStatsEngine class
- **`mqtt_client.py`**: MQTT subscription handling and message routing (asyncio version)
- **`web_server.py`**: Flask application with production dashboard and REST APIs
- **`simulator.py`**: Firewood splitter simulator for testing and development
- **`config.py`**: Configuration management for MQTT settings and production parameters
- **`templates/production_dashboard.html`**: Live production monitoring web interface
- **`.env`**: MQTT broker credentials and production configuration

## Production Statistics Classes
```python
# Core production tracking components
ProductionCycle: Individual splitting operation with timing and status
BasketSession: Collection of 60 splits with completion tracking  
ProductionStatsEngine: Thread-safe statistics aggregation and rate calculation
WindowsMQTTClient: Windows-compatible MQTT client with production message handling
```

## Dependencies & Integration
- **MQTT Libraries**: `paho-mqtt==2.1.0` (Windows-compatible), `aiomqtt==1.0.0` (Linux asyncio)
- **Web Framework**: `Flask==3.1.2` with threading support for concurrent MQTT/HTTP
- **Configuration**: `python-dotenv==1.0.0` for environment variable management
- **Production Analytics**: Custom classes for firewood splitter-specific calculations
- **Windows Support**: Specific asyncio event loop handling for Windows compatibility

## MQTT Broker Configuration
- **Production Broker**: `159.203.138.46:1883` with authentication
- **Credentials**: Stored in `.env` file (MQTT_USERNAME, MQTT_PASSWORD)
- **Topic Patterns**: `firewood/splitter/001/*` for production data streams
- **Connection Management**: Automatic reconnection with production data buffering

## Testing & Simulation
- **Production Simulator**: Realistic firewood splitter operation simulation with configurable parameters
- **Cycle Timing**: 30-second average cycles with realistic variance
- **Basket Tracking**: 60 splits per basket with 30-minute completion time
- **Resource Simulation**: Fuel consumption (0.25 gallons per basket)
- **Rate Validation**: Production rates of 100-120 splits/hour typical

## Windows Deployment Notes
- **Event Loop Policy**: Uses `WindowsProactorEventLoopPolicy` for asyncio compatibility
- **Synchronous MQTT**: `main_windows.py` uses blocking MQTT client to avoid Windows asyncio issues
- **Threading Model**: Flask web server runs in separate thread from MQTT message processing
- **Process Management**: Handle Windows-specific signal handling and graceful shutdown

## Performance & Monitoring
- **Production Metrics**: Real-time calculation of splits/hour, baskets/hour, cycle efficiency
- **Memory Management**: Efficient storage of production cycles with configurable retention
- **Thread Safety**: All statistics operations are thread-safe for concurrent MQTT/HTTP access
- **Dashboard Updates**: Live web interface updates without page refresh
- **API Endpoints**: RESTful APIs for production data integration with other systems

## Industrial Integration
- **Controller Compatibility**: Designed for embedded IoT controllers on hydraulic log splitters
- **Production Scaling**: Supports multiple splitter monitoring with topic pattern expansion
- **Maintenance Integration**: Tracks operational hours, split counts for service scheduling
- **Efficiency Analysis**: Production rate trending and performance optimization insights