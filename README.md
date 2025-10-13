# Firewood Splitter Production Monitor

A specialized Python application for monitoring commercial firewood splitter operations in real-time. This system connects to MQTT-enabled firewood splitter controllers to track production cycles, calculate efficiency metrics, and provide live dashboard monitoring for industrial operations.

## 🏭 Industrial Overview

This system is designed for **commercial firewood production facilities** using hydraulic log splitters equipped with IoT controllers. It provides real-time monitoring of:

- **Production Cycles**: Individual log splitting operations (30-second average)
- **Basket Sessions**: Collections of 60 splits per basket (30-minute sessions)
- **Production Rates**: Splits per hour, baskets per hour, efficiency tracking
- **Resource Monitoring**: Fuel consumption, maintenance intervals, operational status

## 🚀 Deployment Guide

### Prerequisites

**All Systems:**
- Python 3.11+
- Git (for repository cloning)
- MQTT broker access (credentials required)
- Network connectivity to MQTT broker

**Windows Specific:**
- Windows 10/11 (optimized for Windows deployment)
- PowerShell (recommended terminal)

**Debian/Ubuntu Specific:**
- Debian 11+, Ubuntu 20.04+, or Raspberry Pi OS
- Bash terminal access
- sudo privileges for system packages

---

## 🖥️ Windows Deployment

### Step 1: System Prerequisites

```powershell
# Verify Python installation
python --version
# Should show Python 3.11+ 

# If Python not installed, download from python.org
# Make sure to check "Add Python to PATH" during installation
```

### Step 2: Clone Repository

```powershell
# Clone from GitHub
git clone https://github.com/Alex-Pennington/stats_splitter_python.git
cd stats_splitter_python

# Verify files are present
dir
```

### Step 3: Environment Setup

```powershell
# Create virtual environment (recommended)
python -m venv splitter_env
splitter_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure MQTT credentials
copy template.env .env
# Edit .env with your actual credentials:
# - Replace YOUR_BROKER_IP_HERE with: 159.203.138.46
# - Replace YOUR_USERNAME_HERE with: rayven  
# - Replace YOUR_PASSWORD_HERE with: [your password]
```

### Step 4: Run the System

```powershell
# Start the production monitor
python main_windows.py

# In a new PowerShell window, test with simulator
python simulator.py --duration 5 --speed 2

# Access the dashboard
# http://localhost:5000 - Live dashboard
# http://localhost:5000/api/production/summary - API endpoint
```

### Step 5: Windows Firewall Configuration

```powershell
# Allow Python through Windows Firewall (if needed)
# Windows Security > Firewall & network protection > Allow an app
# Add Python.exe to allowed apps for port 5000
```

---

## 🐧 Debian/Ubuntu Deployment

### Step 1: System Prerequisites

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install python3 python3-pip python3-venv git -y

# Verify Python version
python3 --version
# Should show Python 3.11+
```

### Step 2: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/Alex-Pennington/stats_splitter_python.git
cd stats_splitter_python

# Verify files are present
ls -la
```

### Step 3: Environment Setup

```bash
# Create virtual environment (recommended)
python3 -m venv splitter_env
source splitter_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure MQTT credentials
cp template.env .env
# Edit .env with your actual credentials:
nano .env
# - Replace YOUR_BROKER_IP_HERE with: 159.203.138.46
# - Replace YOUR_USERNAME_HERE with: rayven
# - Replace YOUR_PASSWORD_HERE with: [your password]
```

### Step 4: Run the System

```bash
# Start the production monitor
python3 main_windows.py

# In a new terminal, test with simulator
python3 simulator.py --duration 5 --speed 2

# Access the dashboard
# http://localhost:5000 - Live dashboard
# http://localhost:5000/api/production/summary - API endpoint
```

### Step 5: Network Access Setup

```bash
# For remote access from other farm devices:
# Find your IP address
ip addr show | grep inet

# Access from other devices using your IP:
# http://YOUR-DEBIAN-IP:5000

# Optional: Configure firewall (UFW)
sudo ufw allow 5000/tcp
sudo ufw enable
```

---

## 🔧 Production Service Setup (Linux Only)

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/firewood-splitter.service
```

Service configuration:
```ini
[Unit]
Description=Firewood Splitter Production Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/stats_splitter_python
Environment=PATH=/home/pi/stats_splitter_python/splitter_env/bin
ExecStart=/home/pi/stats_splitter_python/splitter_env/bin/python main_windows.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
# Enable service
sudo systemctl enable firewood-splitter.service
sudo systemctl start firewood-splitter.service

# Check status
sudo systemctl status firewood-splitter.service

# View logs
sudo journalctl -u firewood-splitter.service -f
```

---

## 🚜 Farm Network Access

### Local Network Configuration

**For Windows:**
```powershell
# Find your IP address
ipconfig | findstr IPv4

# Share access with other farm devices:
# http://YOUR-WINDOWS-IP:5000
```

**For Debian/Linux:**
```bash
# Find your IP address
hostname -I

# Share access with other farm devices:
# http://YOUR-LINUX-IP:5000
```

### Mobile Device Access

- **Tablets/Phones**: Navigate to `http://farm-computer-ip:5000`
- **Responsive Design**: Dashboard adapts to mobile screens
- **Farm WiFi**: Ensure all devices on same network

---

## ✅ Verification Steps

### Test System Functionality

**Both Systems:**
```
1. ✅ Repository cloned successfully
2. ✅ Dependencies installed without errors  
3. ✅ .env file configured with MQTT credentials
4. ✅ main_windows.py starts without errors
5. ✅ Web dashboard accessible at http://localhost:5000
6. ✅ Simulator produces realistic production data
7. ✅ MQTT connection established successfully
8. ✅ Production statistics updating in real-time
```

### Common Troubleshooting

**Connection Issues:**
```bash
# Test MQTT broker connectivity
ping 159.203.138.46

# Check credentials in .env file
cat .env | grep MQTT
```

**Permission Issues (Linux):**
```bash
# Fix ownership of project directory
sudo chown -R $USER:$USER /path/to/stats_splitter_python
```

**Port 5000 Already in Use:**
```bash
# Find process using port 5000
netstat -tulpn | grep 5000
# Kill process or change WEB_PORT in .env
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

The included simulator generates realistic firewood splitter data based on real farm timing patterns:

```powershell
# Run 5-minute simulation at 2x speed
python simulator.py --duration 5 --speed 2

# Standard production simulation
python simulator.py --duration 60 --speed 1
```

### Simulator Command Line Flags

The simulator accepts the following command line arguments:

#### Connection Parameters

```powershell
# MQTT broker settings (defaults to .env values)
--host          # MQTT broker IP (default: from .env MQTT_BROKER)
--port          # MQTT broker port (default: from .env MQTT_PORT)
--username      # MQTT username (default: from .env MQTT_USERNAME) 
--password      # MQTT password (default: from .env MQTT_PASSWORD)
```

#### Simulation Control

```powershell
--duration      # Simulation duration in minutes (default: 10)
--speed         # Speed multiplier 1.0-10.0x (default: 1.0)
--splits-per-basket  # Splits per basket (default: 60)
--cycle-time    # Average cycle time in seconds (default: 30.0)
```

#### Example Usage Commands

**Quick Test (5 minutes at 2x speed):**

```powershell
python simulator.py --duration 5 --speed 2
```

**Extended Production Test (30 minutes at normal speed):**

```powershell
python simulator.py --duration 30 --speed 1
```

**Fast Development Testing (2 minutes at 10x speed):**

```powershell
python simulator.py --duration 2 --speed 10
```

**Custom Basket Size Testing:**

```powershell
python simulator.py --duration 15 --splits-per-basket 40 --cycle-time 25
```

**Override MQTT Connection:**

```powershell
python simulator.py --host 192.168.1.100 --port 1883 --username testuser --password testpass --duration 10
```

### Realistic Farm Timing Patterns

The simulator uses real farm data patterns:

- **Extend Time**: 5-7 seconds (average 6.1s) - hydraulic cylinder extending
- **Retract Time**: 4-6 seconds (average 5.5s) - cylinder retracting after split
- **Gap Time**: 2-8 seconds (average 5.1s) - positioning next log
- **Abort Rate**: 7% - realistic failure/retry rate from farm operations
- **Total Cycle**: ~17 seconds average (matches real farm timing)

### Simulation Parameters

- **Cycle Time**: 30 seconds average with realistic variance
- **Basket Completion**: 60 splits per basket (30 minutes)
- **Fuel Consumption**: 0.25 gallons per completed basket
- **Production Rate**: 100-120 splits/hour typical
- **MQTT Topics**: Uses LogSplitter Controller topic structure:
  - `controller/sequence/+` - Cycle sequence data
  - `controller/pressure/+` - Hydraulic pressure readings
  - `controller/relays/+/state` - Relay state changes

## 🖥️ Windows Optimization

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
 
 