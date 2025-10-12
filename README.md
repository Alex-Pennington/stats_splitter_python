# Firewood Splitter Production Monitor

A specialized Python application for monitoring commercial firewood splitter operations in real-time. This system connects to MQTT-enabled firewood splitter controllers to track production cycles, calculate efficiency metrics, and provide live dashboard monitoring for industrial operations.

## 🏭 Industrial Overview

This system is designed for **commercial firewood production facilities** using hydraulic log splitters equipped with IoT controllers. It provides real-time monitoring of:

- **Production Cycles**: Individual log splitting operations (30-second average)
- **Basket Sessions**: Collections of 60 splits per basket (30-minute sessions)
- **Production Rates**: Splits per hour, baskets per hour, efficiency tracking
- **Resource Monitoring**: Fuel consumption, maintenance intervals, operational status

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MQTT broker access (credentials required)
- Windows 10/11 (optimized for Windows deployment)

### Installation

```powershell
# Clone the repository
git clone <repository-url>
cd stats_splitter_python

# Install dependencies
pip install -r requirements.txt

# Configure MQTT credentials (create .env file)
# MQTT_BROKER=your.broker.address
# MQTT_PORT=1883
# MQTT_USERNAME=your_username
# MQTT_PASSWORD=your_password
```

### Running the System

```powershell
# Start the main production monitor (Windows-compatible)
python main_windows.py

# In another terminal, run the simulator for testing
python simulator.py --duration 10 --speed 2

# Access the dashboard
# http://localhost:5000 - Live dashboard
# http://localhost:5000/api/production/summary - API endpoint
```

## 📊 System Architecture

### Core Components

- **`main_windows.py`**: Windows-compatible main application with synchronous MQTT
- **`production_stats.py`**: Production analytics engine with cycle and basket tracking
- **`web_server.py`**: Flask web server with live dashboard and REST APIs
- **`simulator.py`**: Realistic firewood splitter operation simulator
- **`mqtt_client.py`**: Asyncio-based MQTT client (Linux/advanced use)

### MQTT Topic Structure

The system monitors 6 production-specific topics:

```
firewood/splitter/001/cycle_start      - Production cycle initiation
firewood/splitter/001/split_complete   - Individual split completion
firewood/splitter/001/basket_status    - Basket fill status updates
firewood/splitter/001/engine_stats     - Engine performance metrics
firewood/splitter/001/hydraulic_pressure - Hydraulic system data
firewood/splitter/001/maintenance_alert - Service notifications
```

## 🔧 Production Statistics

### Key Metrics Tracked

- **Cycle Efficiency**: Time per split, cycle completion rates
- **Production Volume**: Total splits, completed baskets
- **Resource Usage**: Fuel consumption (0.25 gallons per basket)
- **Performance Rates**: Real-time splits/hour, baskets/hour calculations
- **Operational Status**: Equipment health, maintenance alerts

### Data Classes

```python
ProductionCycle    # Individual splitting operation tracking
BasketSession      # Collection of 60 splits with timing
ProductionStatsEngine  # Thread-safe statistics aggregation
```

## 🌐 Web Dashboard

The live dashboard provides:

- **Real-time Production Metrics**: Current cycle status, completion rates
- **Historical Analytics**: Production trends, efficiency analysis
- **REST API Endpoints**: Integration with other systems
- **Resource Monitoring**: Fuel levels, maintenance schedules

Access at: `http://localhost:5000`

## 🧪 Testing & Simulation

### Production Simulator

The included simulator generates realistic firewood splitter data:

```powershell
# Run 5-minute simulation at 2x speed
python simulator.py --duration 5 --speed 2

# Standard production simulation
python simulator.py --duration 60 --speed 1
```

### Simulation Parameters

- **Cycle Time**: 30 seconds average with realistic variance
- **Basket Completion**: 60 splits per basket (30 minutes)
- **Fuel Consumption**: 0.25 gallons per completed basket
- **Production Rate**: 100-120 splits/hour typical

## 🖥️ Windows Deployment

This system is optimized for Windows environments:

- **Synchronous MQTT**: Uses `paho-mqtt` for Windows compatibility
- **Event Loop Handling**: Proper Windows asyncio event loop management
- **Threading Model**: Separate threads for MQTT and web server
- **Signal Handling**: Windows-specific graceful shutdown

## 📈 Industrial Integration

### Scaling for Multiple Splitters

The system can be extended to monitor multiple splitters:

- Topic patterns: `firewood/splitter/{001-999}/*`
- Dashboard filtering by splitter ID
- Aggregated production reporting

### Maintenance Integration

- **Operational Hours**: Track runtime for service scheduling
- **Split Count Monitoring**: Maintenance intervals based on usage
- **Performance Degradation**: Early warning for efficiency drops

## 🚜 Farm Deployment

This system is designed for remote farm operations:

- **Reliable MQTT Connection**: Handles intermittent connectivity
- **Local Data Storage**: Maintains statistics during network outages
- **Mobile Dashboard**: Responsive web interface for tablet/phone access
- **Production Reporting**: End-of-shift and daily production summaries

---

**Industrial Firewood Production Monitoring System**  
*Real-time analytics for commercial log splitting operations*