# LogSplitter Monitor Command Reference# LogSplitter Monitor Command Reference



## Overview## Overview



This document provides a comprehensive reference for all available commands in the LogSplitter Monitor system. Commands can be executed via:This document provides a comprehensive reference for all available commands in the LogSplitter Monitor system. Commands can be executed via:



- **Telnet**: Connect to port 23 (`telnet <monitor_ip> 23`)- **Telnet**: Connect to port 23 (`telnet <monitor_ip> 23`)

- **MQTT**: Send commands to `r4/monitor/control` topic- **MQTT**: Send commands to `r4/monitor/control` topic

- **Serial Console**: Direct serial connection during development- **Serial Console**: Direct serial connection during development



All commands are case-insensitive and have a rate limit of 10 commands per second to prevent system overload.All commands are case-insensitive and have a rate limit of 10 commands per second to prevent system overload.



## Command Categories## Command Categories



### System Information Commands### System Information Commands



#### `help`#### `help`



**Description**: Display all available commands  **Description**: Display all available commands  

**Usage**: `help`  **Usage**: `help`  

**Response**: Complete list of available commands with syntax  **Response**: Complete list of available commands with syntax  



**Example**:**Example**:



```bash```bash

> help> help

Available commands:Available commands:

help           - Show this helphelp           - Show this help

show           - Show sensor readingsshow           - Show sensor readings

status         - Show system statusstatus         - Show system status

network        - Show network statusnetwork        - Show network status

debug [on|off] - Toggle debug modedebug [on|off] - Toggle debug mode

loglevel [0-7] - Set logging level (0=EMERGENCY, 7=DEBUG)loglevel [0-7] - Set logging level (0=EMERGENCY, 7=DEBUG)

monitor start  - Start monitoringmonitor start  - Start monitoring

weight read    - Read current weightweight read    - Read current weight

temp read      - Read temperature sensors (Fahrenheit)temp read      - Read temperature sensors (Fahrenheit)

lcd on|off     - Turn LCD display on/offlcd on|off     - Turn LCD display on/off

i2c scan       - Scan Wire1 I2C bus for devicesi2c scan       - Scan Wire1 I2C bus for devices

test network   - Test network connectivitytest network   - Test network connectivity

syslog test    - Send test syslog messagesyslog test    - Send test syslog message

reset system   - Restart the devicereset system   - Restart the device

``````



#### `show`#### `show`

**Description**: Display current sensor readings and system status  

**Description**: Display current sensor readings and system status  **Usage**: `show`  

**Usage**: `show`  **Response**: Formatted sensor data and system state  

**Response**: Formatted sensor data and system state  

**Example**:

**Example**:

```bash

```bash> show

> showTemperature: Local=72.5°F Remote=145.2°F

Temperature: Local=72.5°F Remote=145.2°FWeight: 125.340 lbs (filtered: 125.335)

Weight: 125.340 lbs (filtered: 125.335)Voltage: 5.02V

Voltage: 5.02VSystem: MONITORING, Uptime: 3h25m

System: MONITORING, Uptime: 3h25m```

```

#### `status`

#### `status`**Description**: Enable or disable debug output to serial console

**Syntax**: `debug [ON|OFF]`

**Description**: Show detailed system and network status  **Access**: Serial + MQTT

**Usage**: `status`  

**Response**: Network connectivity, system state, and component health  **Examples**:

```

**Example**:> debug

debug OFF

```bash

> status> debug ON

Network: WiFi=CONNECTED, MQTT=CONNECTED, Syslog=WORKINGdebug ON

Monitor: MONITORING, Sensors=OK, LCD=ON

```> debug off

debug OFF

#### `network````



**Description**: Show network connection health and details  **Note**: Debug output is **disabled by default** to reduce serial console noise. When enabled, the system outputs detailed diagnostic information including:

**Usage**: `network`  - Input pin state changes

**Response**: WiFi signal strength, IP address, connection status  - Limit switch activations  

- MQTT message details

**Example**:- Pressure sensor initialization

- Command processing status

```bash

> network### 4. NETWORK

WiFi: CONNECTED, IP=192.168.1.150, Signal=-45dBm**Description**: Display network health statistics and connection status

MQTT: CONNECTED, Broker=159.203.138.46:1883**Syntax**: `network`

Syslog: ACTIVE, Server=192.168.1.238:514**Access**: Serial + MQTT

```

**Example Output**:

### Configuration Commands```

> network

#### `set <parameter> <value>`wifi=OK mqtt=OK stable=YES disconnects=2 fails=0 uptime=1247s

```

**Description**: Configure system parameters  

**Parameters**:**Status Fields**:

- **wifi**: OK/DOWN - WiFi connection state

- `debug <on|off>` - Enable/disable debug output- **mqtt**: OK/DOWN - MQTT broker connection state  

- `loglevel <0-7>` - Set logging level (0=EMERGENCY, 7=DEBUG)- **stable**: YES/NO - Connection stable for >30 seconds

- `syslog <ip[:port]>` - Set syslog server address- **disconnects**: Total number of connection losses

- `mqtt <host[:port]>` - Set MQTT broker address- **fails**: Failed MQTT publish attempts

- `interval <ms>` - Set status publish interval (1000-300000 ms)- **uptime**: Current connection uptime in seconds

- `heartbeat <ms>` - Set heartbeat publish interval (5000-600000 ms)

**Network Failsafe Operation**:

**Examples**:- ✅ **Hydraulic control NEVER blocked by network issues**

- ✅ **Non-blocking reconnection** - system continues operating during network problems

```bash- ✅ **Automatic recovery** with exponential backoff

> set debug on- ✅ **Connection stability monitoring** prevents flapping

debug ON- ✅ **Health metrics** for diagnostics and troubleshooting



> set loglevel 6### 5. RESET

Log level set to 6 (INFO)**Description**: Reset system components from fault states or perform complete system reboot

**Syntax**: `reset <component>`

> set syslog 192.168.1.238:514**Access**: Serial + MQTT

syslog server set to 192.168.1.238:514

#### Available RESET Components:

> set interval 10000

publish interval set to 10000 ms##### Emergency Stop (E-Stop) Reset

```**Parameter**: `estop`

**Function**: Clear emergency stop latch and restore system operation

#### `debug [on|off]`

**Requirements**:

**Description**: Toggle or check debug mode status  - Emergency stop button must NOT be currently pressed

**Usage**: `debug` (show status) or `debug <on|off>` (set state)  - System must be in emergency stop state (SYS_EMERGENCY_STOP)



**Examples**:**Examples**:

```

```bash> reset estop

> debugE-Stop reset successful - system operational

debug OFF

> reset estop

> debug onE-Stop reset failed: E-Stop button still pressed

debug ON

```> reset estop  

E-Stop not latched - no reset needed

#### `loglevel [0-7|get|list]````



**Description**: Control logging severity levels  **Safety Notes**:

**Usage**: - ⚠️ **CRITICAL**: E-Stop reset requires manual verification that all hazards are clear

- `loglevel` - Show current level- ⚠️ **VERIFY**: Ensure E-Stop button is physically released before attempting reset

- `loglevel <0-7>` - Set specific level- ⚠️ **CONFIRM**: All personnel are clear of hydraulic equipment before reset

- `loglevel get` - Show current level with name- ✅ Reset only clears the software latch - hardware E-Stop must be manually released

- `loglevel list` - Show all available levels- ✅ Safety system integration prevents unsafe operation



**Log Levels**:##### Complete System Reset

**Parameter**: `system`

- `0` - EMERGENCY (System unusable)**Function**: Perform complete system reboot equivalent to power cycling

- `1` - ALERT (Immediate action required)

- `2` - CRITICAL (Critical conditions)**Examples**:

- `3` - ERROR (Error conditions)```

- `4` - WARNING (Warning conditions)> reset system

- `5` - NOTICE (Normal but significant)System reset initiated - rebooting...

- `6` - INFO (Informational - default)[System reboots immediately]

- `7` - DEBUG (Debug-level messages)```



**Examples**:**Reset Effects**:

- **Complete Hardware Reset**: Equivalent to power off/on cycle

```bash- **All Variables Reset**: All runtime variables return to default values

> loglevel- **Network Reconnection**: WiFi and MQTT connections will be re-established

Current log level: 6 (INFO)- **Configuration Preserved**: EEPROM settings remain intact

- **Immediate Effect**: System reboots within ~100ms of command execution

> loglevel 7

Log level set to 7 (DEBUG)**Use Cases**:

- Recovery from system lockup or unresponsive state

> loglevel list- Clearing memory corruption or stack overflow issues

Log levels: 0=EMERGENCY, 1=ALERT, 2=CRITICAL, 3=ERROR, 4=WARNING, 5=NOTICE, 6=INFO, 7=DEBUG- Full system refresh after configuration changes

```- Emergency recovery when other reset methods fail



### Sensor Commands**Safety Notes**:

- ⚠️ **WARNING**: All active hydraulic operations will stop immediately

#### Weight Sensor (NAU7802)- ⚠️ **VERIFY**: Ensure hydraulic cylinders are in safe position before reset

- ✅ Safety systems will reinitialize with full protection on reboot

##### `weight <subcommand>`- ✅ E-Stop state will be re-evaluated on startup



**Description**: Interact with the precision weight sensor  ### 6. PINS

**Subcommands**:**Description**: Display current PIN mode configuration for all Arduino pins

**Syntax**: `pins`

- `read` - Get current weight readings**Access**: Serial + Telnet ONLY (Security restriction)

- `raw` - Get raw ADC values

- `tare` - Tare the scale at current load**Example Output**:

- `zero` - Zero calibration (no load)```

- `calibrate <weight>` - Scale calibration with known weight> pins

- `status` - Show sensor status and readingsPin 0: INPUT_PULLUP

- `save` - Save calibration to EEPROMPin 1: OUTPUT

- `load` - Load calibration from EEPROMPin 2: INPUT

...

**Examples**:Pin 13: OUTPUT

```

```bash

> weight read### 7. SET

weight: 125.340 (filtered: 125.335)**Description**: Configure system parameters with EEPROM persistence

**Syntax**: `set <parameter> <value>`

> weight raw**Access**: Serial + MQTT

raw weight: 8429742

#### Available SET Parameters:

> weight zero

zero calibration completed##### Pressure Sensor Configuration

- **vref** - ADC reference voltage (volts, default: 4.5)

> weight calibrate 500.0  ```

scale calibrated with weight 500.00  > set vref 4.5

  set vref=4.5

> weight status  ```

status: OK, ready: YES, weight: 125.340, raw: 8429742

- **maxpsi** - Maximum pressure scale (PSI, default: 5000)

> weight save  ```

weight calibration saved to EEPROM  > set maxpsi 5000

```  set maxpsi=5000

  ```

#### Temperature Sensor (MCP9600)

- **gain** - Pressure sensor gain multiplier (default: 1.0)

##### `temp <subcommand>` (alias: `temperature`)  ```

  > set gain 1.0

**Description**: Read thermocouple temperature sensor    set gain=1.0

**Subcommands**:  ```



- `read` - Read both sensors in Fahrenheit- **offset** - Pressure sensor offset (PSI, default: 0.0)

- `readc` - Read both sensors in Celsius  ```

- `local` - Local/ambient temperature (°F)  > set offset 0.0

- `localc` - Local/ambient temperature (°C)  set offset=0.0

- `remote` - Remote/thermocouple temperature (°F)  ```

- `remotec` - Remote/thermocouple temperature (°C)

- `status` - Show sensor status and diagnostics- **filter** - Digital filter coefficient (0.0-1.0, default: 0.8)

- `offset <local> <remote>` - Set temperature offsets in Celsius  ```

  > set filter 0.8

**Examples**:  set filter=0.8

  ```

```bash

> temp read- **emaalpha** - Exponential Moving Average alpha (0.0-1.0, default: 0.1)

local: 72.50°F, remote: 145.20°F  ```

  > set emaalpha 0.1

> temp readc  set emaalpha=0.1

local: 22.78°C, remote: 62.89°C  ```



> temp local##### Individual Sensor Configuration

local temperature: 72.50°FConfigure sensors independently with sensor-specific parameters:



> temp status**A1 System Pressure Sensor (4-20mA Current Loop)**:

MCP9600: READY, Local=72.5°F Remote=145.2°F- **a1_maxpsi** - Maximum pressure range (PSI, default: 5000)

- **a1_vref** - ADC reference voltage (volts, default: 5.0)

> temp offset 0.5 -1.0- **a1_gain** - Sensor gain multiplier (default: 1.0)

temperature offsets set: local=0.50°C, remote=-1.00°C- **a1_offset** - Sensor offset (PSI, default: 0.0)

```

**A5 Filter Pressure Sensor (0-4.5V Voltage Output)**:

### Visual System Commands- **a5_maxpsi** - Maximum pressure range (PSI, default: 30 for 0-30 PSI absolute sensor)

- **a5_vref** - ADC reference voltage (volts, default: 5.0)

#### LCD Display Control- **a5_gain** - Sensor gain multiplier (default: 1.0, note: sensor outputs 0-4.5V for full scale)

- **a5_offset** - Sensor offset (PSI, default: 0.0)

##### `lcd <subcommand>`

Examples:

**Description**: Control 20x4 LCD display  ```

**Subcommands**:> set a1_maxpsi 5000

A1 maxpsi set 5000

- (no parameter) - Show LCD status

- `on` - Enable LCD display> set a5_maxpsi 3000

- `off` - Disable LCD displayA5 maxpsi set 3000

- `clear` - Clear LCD screen

- `backlight <on|off>` - Control backlight> set a5_gain 1.2

- `info <message>` - Display custom messageA5 gain set 1.200000

- `test` - Display test pattern

- `reinit` - Reinitialize LCD hardware> set a5_offset -10.5

- `refresh` - Force update with current sensor dataA5 offset set -10.500000

```

**Examples**:

##### Sequence Controller Configuration

```bash- **seqstable** - Sequence stability time in milliseconds (default: 15)

> lcd  ```

LCD status: ON, backlight: ON  > set seqstable 15

  set seqstable=15

> lcd off  ```

LCD display disabled

- **seqstartstable** - Sequence start stability time in milliseconds (default: 100)

> lcd clear  ```

LCD display cleared  > set seqstartstable 100

  set seqstartstable=100

> lcd backlight off  ```

LCD backlight disabled

- **seqtimeout** - Sequence timeout in milliseconds (default: 30000)

> lcd info "System OK"  ```

LCD info message displayed  > set seqtimeout 30000

  set seqtimeout=30000

> lcd refresh  ```

LCD refreshed: F=125.3gal T=72.5°F

```##### PIN Configuration (Serial Only)

- **pinmode** - Configure Arduino pin mode

#### LED Matrix Heartbeat Animation  **Syntax**: `set pinmode <pin> <mode>`

  **Modes**: INPUT, OUTPUT, INPUT_PULLUP

**Note**: Heartbeat animation is controlled via the `set` command, not as a standalone command.  ```

  > set pinmode 13 OUTPUT

**Heartbeat Control via Set Commands**:  set pinmode pin=13 mode=OUTPUT

  

```bash  > set pinmode 2 INPUT_PULLUP

# Control heartbeat interval (publish frequency, not animation)  set pinmode pin=2 mode=INPUT_PULLUP

set heartbeat <ms>         # Set heartbeat publish interval (5000-600000 ms)  ```

```

##### Debug Control

**Note**: The LED matrix heartbeat animation appears to be controlled by the HeartbeatAnimation class but doesn't have direct command interface in the current implementation.- **debug** - Enable/disable debug output (1/0, ON/OFF, default: OFF)

  ```

### Monitoring and Control Commands  > set debug ON

  set debug=ON

#### `monitor <subcommand>`  

  > set debug 0

**Description**: Control monitoring system operation    set debug=OFF

**Subcommands**:  ```



- `start` - Start monitoring mode##### Syslog Configuration

- `stop` - Enter maintenance mode- **syslog** - Configure rsyslog server IP address and port for centralized logging

- `state` - Show current system state  **Syntax**: `set syslog <ip>` or `set syslog <ip>:<port>`

- `output <1|2> <on|off>` - Control digital outputs  ```

  > set syslog 192.168.1.238

**System States**:  syslog server set to 192.168.1.238:514

  

- `INITIALIZING` - System starting up  > set syslog 192.168.1.100:1514

- `CONNECTING` - Connecting to network  syslog server set to 192.168.1.100:1514

- `MONITORING` - Normal operation (monitoring sensors)  ```

- `ERROR` - System error state  

- `MAINTENANCE` - Maintenance mode  **Notes**:

  - Default port is 514 (standard syslog UDP port)

**Examples**:  - All debug output is sent exclusively to syslog server

  - RFC 3164 compliant format with facility Local0 and severity Info

```bash  - Use `syslog test` to verify connectivity

> monitor start

monitoring started##### MQTT Broker Configuration

- **mqtt** - Configure MQTT broker host and port for real-time telemetry

> monitor stop  **Syntax**: `set mqtt <host>` or `set mqtt <host>:<port>`

monitoring stopped  ```

  > set mqtt 192.168.1.100

> monitor state  mqtt broker set to 192.168.1.100:1883

monitor state: MONITORING (2)  

  > set mqtt broker.example.com:8883

> monitor output 1 on  mqtt broker set to broker.example.com:8883

output 1 set to ON  ```

  

> monitor output 2 off  **Notes**:

output 2 set to OFF  - Default port is 1883 (standard MQTT port)

```  - Change takes effect immediately (disconnects and reconnects)

  - Use `mqtt test` to verify connectivity

### Network and Diagnostic Commands  - Use `mqtt status` to check current configuration



#### `syslog <subcommand>`### 8. SYSLOG

**Description**: Syslog server configuration and testing for centralized logging

**Description**: Test and configure syslog functionality  **Syntax**: `syslog <command>`

**Subcommands**:**Access**: Serial + MQTT



- `test` - Send test message to syslog server#### Syslog Commands:

- `status` - Show syslog server configuration

##### Test Syslog Connection

**Examples**:**Command**: `syslog test`

**Function**: Send a test message to the configured syslog server

```bash

> syslog test**Example**:

syslog test message sent successfully```

> syslog test

> syslog statussyslog test message sent successfully to 192.168.1.238:514

syslog server: 192.168.1.238:514, wifi: connected

```> syslog test

syslog test message failed to send to 192.168.1.238:514

#### `test <component>````



**Description**: Test system components and connectivity  ##### Check Syslog Status

**Components**:**Command**: `syslog status`

**Function**: Display current syslog server configuration and connectivity

- `network` - Test WiFi and MQTT connectivity

- `sensors` - Test all sensor readings**Example Output**:

- `weight` - Test NAU7802 weight sensor specifically```

- `temp` (or `temperature`) - Test temperature sensor specifically> syslog status

- `outputs` - Test digital output pinssyslog server: 192.168.1.238:514, wifi: connected, local IP: 192.168.1.100

- `i2c` - Scan I2C bus for devices```

- `pins` - Test I2C pin functionality

**Syslog Configuration**:

**Examples**:- **Default Server**: 192.168.1.238:514 (configured in constants.h)

- **Protocol**: RFC 3164 compliant UDP syslog

```bash- **Facility**: Local0 (16) for custom application logs

> test network- **Severity**: Info (6) for normal operational messages

network test: wifi=OK mqtt=OK- **Hostname**: "LogSplitter" for easy identification

- **Tag**: "logsplitter" for application identification

> test sensors

sensor test: local=72.5°F remote=145.2°F**Debug Output Integration**:

- All debugPrintf() messages are sent exclusively to the syslog server

> test weight- No local debug output to Serial or Telnet (cleaner operation)

weight test: status=OK ready=YES weight=125.340 raw=8429742- Configure syslog server with `set syslog <ip>` or `set syslog <ip>:<port>`

- Test connectivity with `syslog test` command

> test i2c

i2c test: found 4 device(s) on Wire1: 0x27 (LCD) 0x2A (NAU7802) 0x67 (MCP9600) 0x70 (I2C Mux)### 9. MQTT

```**Description**: MQTT broker configuration and testing for real-time telemetry

**Syntax**: `mqtt <command>`

#### `i2c <subcommand>`**Access**: Serial + MQTT



**Description**: I2C bus diagnostic and management  #### MQTT Commands:

**Subcommands**:

##### Test MQTT Connection

- `scan` - Scan Wire1 I2C bus for devices**Command**: `mqtt test`

- `status` - Show I2C bus configuration**Function**: Send a test message to the configured MQTT broker

- `show` - List expected device addresses

- `mux` - Scan through TCA9548A multiplexer channels**Example**:

```

**Expected I2C Devices**:> mqtt test

mqtt test message sent successfully to 159.203.138.46:1883

- `0x2A` - NAU7802 Load Cell Sensor

- `0x27/0x3F` - LCD Display> mqtt test

- `0x60/0x67` - MCP9600 Thermocouple SensorMQTT not connected to broker 159.203.138.46:1883

- `0x40-0x4F` - INA219 Power Monitor (if present)```

- `0x68` - MCP3421 ADC (if present)

- `0x70` - TCA9548A I2C Multiplexer##### Check MQTT Status

**Command**: `mqtt status`

**Examples**:**Function**: Display current MQTT broker configuration and connectivity



```bash**Example Output**:

> i2c scan```

I2C Scan Results (Wire1):> mqtt status

Device found at 0x27 (LCD Display)mqtt broker: 159.203.138.46:1883, wifi: connected, mqtt: connected, local IP: 192.168.1.100

Device found at 0x2A (NAU7802 Load Cell)```

Device found at 0x67 (MCP9600 Thermocouple)

Device found at 0x70 (TCA9548A I2C Mux)**MQTT Configuration**:

Total devices found: 4- **Default Broker**: 159.203.138.46:1883 (configured in constants.h)

- **Protocol**: MQTT v3.1.1 over TCP

> i2c mux- **Client ID**: Automatically generated from MAC address (format: r4-XXXXXX)

Scanning through TCA9548A channels:- **Topics**: Hierarchical structure under `/controller` namespace

Ch0: none- **Authentication**: Optional username/password support (if configured)

Ch1: 0x2A (NAU7802)

Ch2: 0x67 (MCP9600)**Runtime Configuration**:

Ch3: none- Configure MQTT broker with `set mqtt <host>` or `set mqtt <host>:<port>`

...- Changes take effect immediately (disconnects and reconnects to new broker)

```- Test connectivity with `mqtt test` command

- Monitor status with `mqtt status` command

### System Control Commands

### 10. ERROR

#### `reset <target>`**Description**: System error management for diagnostics and maintenance

**Syntax**: `error <command> [parameter]`

**Description**: Reset system components  **Access**: Serial + MQTT

**Targets**:

#### Error Commands:

- `system` - Restart the entire device

- `network` - Reset network connections##### List Active Errors

**Command**: `error list`

**Examples**:**Function**: Display all currently active system errors with acknowledgment status



```bash**Example Output**:

> reset system```

system reset requested - restarting...> error list

Active errors: 0x01:(ACK)EEPROM_CRC, 0x10:CONFIG_INVALID

> reset network```

network reset requested

```##### Acknowledge Error

**Command**: `error ack <error_code>`

## Command Response Format**Function**: Acknowledge a specific error (changes LED pattern but doesn't clear error)



All commands return text responses that indicate:**Error Codes**:

- `0x01` - EEPROM CRC validation failed

- **Success**: Operation completed successfully with result data- `0x02` - EEPROM save operation failed  

- **Error**: Error message with specific failure reason- `0x04` - Pressure sensor malfunction

- **Usage**: Syntax help for incorrect command usage- `0x08` - Network connection persistently failed

- `0x10` - Configuration parameters invalid

## Rate Limiting- `0x20` - Memory allocation issues

- `0x40` - General hardware fault

Commands are limited to **10 per second** to prevent system overload. If rate limit is exceeded:- `0x80` - Sequence operation timeout



```bash**Examples**:

> command```

rate limited> error ack 0x01

```Error 0x01 acknowledged



## MQTT Command Interface> error ack 0x10

Error 0x10 acknowledged

Commands can be sent via MQTT:```



- **Command Topic**: `r4/monitor/control`##### Clear All Errors

- **Response Topic**: `r4/monitor/control/resp`**Command**: `error clear`

- **Format**: Send command exactly as you would via telnet**Function**: Clear all system errors (only if underlying faults are resolved)



**Example MQTT Command**:**Example**:

```

```bash> error clear

# Send commandAll errors cleared

mosquitto_pub -h broker.example.com -t "r4/monitor/control" -m "weight read"```



# Response will be published to##### Safety Clear vs Error Clear

# Topic: r4/monitor/control/resp**Safety Clear (Pin 4 Button)**:

# Message: "weight: 125.340 (filtered: 125.335)"- **Purpose**: Operational recovery - allows resuming normal operation

```- **Action**: Clears safety system lockouts and re-enables sequence controller after timeout

- **Error History**: Preserves all error records for management review

## Missing Commands (Planned/Incomplete)- **Sequence Control**: Re-enables sequence controller if disabled due to timeout errors

- **Use Case**: Managing operator restores operation after addressing fault causes

Based on documentation references, these commands may be planned but not currently implemented:

**Error Clear (Command)**:

### Power Sensor Commands (INA219)- **Purpose**: Error history management - clears error records

- **Action**: Removes error entries from system error list

- `power read` - Read all power measurements  - **Safety State**: Does not affect safety system lockouts

- `power voltage` - Read bus voltage only  - **Use Case**: Management clears error history after review and documentation

- `power current` - Read current only  

- `power watts` - Read power consumption  **Typical Recovery Sequence**:

- `power status` - Show power sensor status  1. Fault occurs → Safety system activates → Mill light indicates errors

2. **Sequence Timeout**: If timeout occurs, sequence controller is disabled

### Heartbeat Animation Commands3. Operator addresses root cause of fault condition

4. Manager presses Safety Clear (Pin 4) → System operational, sequence re-enabled, errors still logged

- `heartbeat on/off` - Enable/disable LED matrix animation  5. Manager reviews error list → Documents incident → Issues `error clear` command

- `heartbeat rate <bpm>` - Set animation rate (30-200 BPM)  

- `heartbeat brightness <0-255>` - Set LED brightness  **System Error LED (Pin 9)**:

- `heartbeat status` - Show animation status  - **OFF**: No errors

- **Solid ON**: Single error or all errors acknowledged

*Note: These commands are referenced in documentation but not found in the current command processor implementation.*- **Slow Blink (1Hz)**: Multiple errors, some unacknowledged

- **Fast Blink (5Hz)**: Critical errors (EEPROM CRC, memory, hardware)

## Error Handling

**MQTT Error Reporting**:

Common error responses:- Error details published to `r4/system/error` topic

- Includes error code, description, and timestamp

- `unknown command: <command>` - Command not recognized- Automatic error reporting on detection

- `invalid command: <command>` - Command failed validation

- `rate limited` - Too many commands sent### 10. RELAY

- `usage: <correct syntax>` - Incorrect command syntax**Description**: Control hydraulic system relays with integrated safety monitoring

- `<component> not available` - Hardware component not initialized**Syntax**: `relay R<number> <state>`

**Access**: Serial + MQTT

## Examples of Complete Command Sessions**Range**: R1-R9 (relays 1-9)

**States**: ON, OFF (case-insensitive)

### Basic System Check

#### Relay Assignments:

```bash- **R1**: Hydraulic Extend Control (Safety-Monitored)

> status- **R2**: Hydraulic Retract Control (Safety-Monitored)

Network: WiFi=CONNECTED, MQTT=CONNECTED, Syslog=WORKING | Monitor: MONITORING, Sensors=OK- **R3-R9**: Direct relay outputs



> show#### Enhanced Manual Operation Safety (R1/R2):

Temperature: Local=72.5°F Remote=145.2°F, Weight: 125.340 lbs, Voltage: 5.02V**Unified Sequence-Based Control**: R1 and R2 commands now use the same intelligent safety system as automatic sequences, providing comprehensive protection against over-travel and pressure damage.



> test network**Pre-Operation Safety Checks:**

network test: wifi=OK mqtt=OK- **Limit Validation**: Commands blocked if already at target limit switch

```- **Pressure Validation**: Commands blocked if pressure already at safety limit

- **System Status**: Commands blocked during active sequences or system faults

### Weight Sensor Calibration

**Real-Time Protection During Operation:**

```bash- **Automatic Limit Shutoff**: 

> weight status  - R1 (Extend) stops when Pin 6 (extend limit) activates

status: OK, ready: YES, weight: 0.000, raw: 8388608  - R2 (Retract) stops when Pin 7 (retract limit) activates

- **Pressure Limit Protection**:

> weight zero  - R1 stops when pressure reaches `EXTEND_PRESSURE_LIMIT_PSI`

zero calibration completed  - R2 stops when pressure reaches `RETRACT_PRESSURE_LIMIT_PSI`

- **Timeout Protection**: Operations abort if timeout exceeded (configurable)

> weight calibrate 500.0

scale calibrated with weight 500.00**Enhanced User Feedback:**

```bash

> weight save# Successful operation start

weight calibration saved to EEPROM> relay R1 ON

manual extend started (safety-monitored)

> weight read

weight: 500.125 (filtered: 500.120)# Safety blocking examples

```> relay R1 ON

manual extend blocked - check limits/pressure/status

### System Configuration

# Manual stop

```bash> relay R1 OFF

> loglevel 7manual operation stopped

Log level set to 7 (DEBUG)

# Non-hydraulic relay (direct control)

> set debug on> relay R3 ON

debug ONrelay R3 ON

```

> set interval 5000

publish interval set to 5000 ms**Safety Messages and Logging:**

- All operations logged with safety status

> set syslog 192.168.1.238- MQTT publishing for remote monitoring

syslog server set to 192.168.1.238:514- Clear feedback on why operations are blocked

```- Integration with system error management



---**Backward Compatibility:**

- Existing command syntax unchanged

**Version**: 1.0  - R3-R9 relays operate as direct control

**Last Updated**: October 2025  - All monitoring and telemetry preserved

**Platform**: Arduino UNO R4 WiFi  

**Firmware**: LogSplitter Monitor v1.1.0## MQTT Data Topics

The controller publishes real-time data to MQTT topics optimized for database integration. Each topic contains a single data value as the payload for streamlined data storage and analysis.

### Pressure Data (Published every 10 seconds)
- **r4/pressure/hydraulic_system** → Hydraulic system pressure (PSI)
- **r4/pressure/hydraulic_filter** → Hydraulic filter pressure (PSI)
- **r4/pressure/hydraulic_system_voltage** → A1 sensor voltage (V)
- **r4/pressure/hydraulic_filter_voltage** → A5 sensor voltage (V)
- **r4/pressure** → Main pressure (backward compatibility)

### System Data (Published every 10 seconds)
- **r4/data/system_uptime** → System uptime (milliseconds)
- **r4/data/safety_active** → Safety system active (1/0)
- **r4/data/estop_active** → E-Stop button pressed (1/0)
- **r4/data/estop_latched** → E-Stop latched state (1/0)
- **r4/data/limit_extend** → Extend limit switch (1/0)
- **r4/data/limit_retract** → Retract limit switch (1/0)
- **r4/data/relay_r1** → Extend relay state (1/0)
- **r4/data/relay_r2** → Retract relay state (1/0)
- **r4/data/splitter_operator** → Splitter operator signal (1/0)

### Sequence Data (Published every 10 seconds)
- **r4/data/sequence_stage** → Current sequence stage (0-2)
- **r4/data/sequence_active** → Sequence running (1/0)
- **r4/data/sequence_elapsed** → Sequence elapsed time (milliseconds)

### Sequence Events (Published on state changes)
- **r4/sequence/event** → Sequence events (start, complete, abort, etc.)
- **r4/sequence/state** → Sequence state changes (start, complete, abort)

### Legacy Topics (Backward Compatibility)
- **r4/sequence/status** → Complex sequence status string
- **r4/example/pub** → Timestamp heartbeat
- **r4/control/resp** → Command responses and system messages

### Database Integration Benefits
- **Simple Values**: Each topic contains only the data value (no parsing required)
- **Consistent Format**: Numeric values as strings, boolean values as 1/0
- **Clear Naming**: Topic name directly indicates the data type
- **Efficient Storage**: Minimal payload overhead for database insertion
- **Scalable**: Easy to add new data points as individual topics

## Safety Features

### Manual Override
The system includes manual safety override capabilities:
- Pressure threshold monitoring (Mid-stroke: 2750 PSI, At limits: 2950 PSI)
- Automatic sequence abort on over-pressure conditions
- Manual override toggle for emergency situations

### Rate Limiting
Commands are rate-limited to prevent system overload:
- Maximum command frequency enforced
- Rate limit violations return "rate limited" response

### Input Validation
All commands undergo strict validation:
- Parameter range checking
- Invalid commands return "invalid command" response
- Malformed relay commands return "relay command failed"

## Hardware Configuration

### Pressure Sensors
- **A1 (Pin A1)**: System hydraulic pressure sensor (4-20mA current loop, 1-5V → 0-5000 PSI)
- **A5 (Pin A5)**: Filter hydraulic pressure sensor (0-5V voltage output → 0-5000 PSI)

### Digital Inputs
- **Pin 6**: Extend limit switch (INPUT_PULLUP)
- **Pin 7**: Retract limit switch (INPUT_PULLUP)
- **Pin 8**: Splitter operator signal (INPUT_PULLUP)
- **Pin 12**: Emergency stop (E-Stop) button (INPUT_PULLUP)

### Relay Outputs
- **Serial1**: Hardware relay control interface
- **R1-R9**: Available relay channels

## Error Responses

| Error | Description |
|-------|-------------|
| `invalid command` | Command not recognized or malformed |
| `invalid parameter` | SET parameter not in allowed list |
| `invalid value` | Parameter value out of range or wrong type |
| `relay command failed` | Relay number invalid or communication error |
| `rate limited` | Commands sent too frequently |
| `pins command not available via MQTT` | PIN commands restricted to serial |

## Example Session

```
> help
Commands: help, show, debug, network, pins, set <param> <val>, relay R<n> ON|OFF

> network
wifi=OK mqtt=OK stable=YES disconnects=0 fails=0 uptime=1247s

> debug
debug OFF

> debug on
debug ON
Debug output enabled

> show
Pressure: Main=0.0 PSI, Hydraulic=0.0 PSI
Sequence: IDLE, Safety: OK
Relays: R1=OFF(RETRACT) R2=OFF(EXTEND)
Safety: Manual Override=OFF, Pressure OK

> set debug OFF
debug OFF

> set maxpsi 4000
set maxpsi=4000

> relay R2 ON
relay R2 ON

> relay R2 OFF  
relay R2 OFF
```

## Development Notes

- All configuration changes are saved to EEPROM for persistence across power cycles
- The system supports both uppercase and lowercase commands
- MQTT responses are published to `r4/control/resp` topic
- Serial responses are sent directly to the console
- PIN mode changes are restricted to serial and telnet interfaces for security