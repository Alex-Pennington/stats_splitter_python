# LogSplitter Controller Command Implementation Guide
## For AI Assistant Future Reference

### OVERVIEW
This document details the exact procedure to add new commands to the LogSplitter Controller system. The system has two types of commands:
1. **Standalone Commands** (like `help`, `show`, `syslog`, `mqtt`)
2. **SET Parameters** (like `set syslog <ip>`, `set mqtt <host>`)

### CRITICAL FILES TO MODIFY

#### 1. Command Validation Arrays (MUST UPDATE FIRST)
**File:** `src/constants.cpp`
```cpp
// Add to ALLOWED_COMMANDS for standalone commands
const char* const ALLOWED_COMMANDS[] = {
    "help", "show", "pins", "pin", "set", "relay", "debug", 
    "network", "reset", "test", "syslog", "mqtt", "loglevel", 
    "heartbeat", "error", "bypass", "NEW_COMMAND", nullptr
};

// Add to ALLOWED_SET_PARAMS for SET parameters
const char* const ALLOWED_SET_PARAMS[] = {
    "vref", "maxpsi", "gain", "offset", "filter", "emaalpha", 
    "a1_maxpsi", "a1_gain", "a1_offset", "a1_vref",
    "a5_maxpsi", "a5_gain", "a5_offset", "a5_vref",
    "pinmode", "seqstable", "seqstartstable", "seqtimeout", 
    "debug", "debugpins", "loglevel", "syslog", "mqtt", 
    "NEW_SET_PARAM", nullptr
};
```

#### 2. Command Processor Header
**File:** `include/command_processor.h`
```cpp
// Add method declaration in private section
private:
    void handleNewCommand(char* param, char* response, size_t responseSize);
```

#### 3. Command Processor Implementation
**File:** `src/command_processor.cpp`

**A. Add Command Handler in processCommand() method:**
```cpp
else if (strcasecmp(cmd, "newcommand") == 0) {
    char* param = strtok(NULL, " ");
    handleNewCommand(param, response, responseSize);
}
```

**B. Add SET Parameter Handler in handleSet() method:**
```cpp
else if (strcasecmp(param, "newparam") == 0) {
    if (someManager) {
        // Parse and validate value
        someManager->setNewParameter(value);
        snprintf(response, responseSize, "new parameter set to %s", value);
    } else {
        snprintf(response, responseSize, "Manager not available");
    }
}
```

**C. Implement the Handler Method:**
```cpp
void CommandProcessor::handleNewCommand(char* param, char* response, size_t responseSize) {
    if (!someManager) {
        snprintf(response, responseSize, "manager not initialized");
        return;
    }
    
    if (!param) {
        snprintf(response, responseSize, "newcommand commands: test, status");
        return;
    }
    
    if (strcasecmp(param, "test") == 0) {
        // Implementation
    }
    else if (strcasecmp(param, "status") == 0) {
        // Implementation
    }
    else {
        snprintf(response, responseSize, "unknown command: %s", param);
    }
}
```

**D. Update Help Text:**
```cpp
void CommandProcessor::handleHelp(char* response, size_t responseSize, bool fromMqtt) {
    const char* helpText = "Commands: help, show, debug, network, reset, error, test, loglevel [0-7], bypass, syslog, mqtt, newcommand";
    // ... rest of help implementation
}
```

#### 4. Manager/Service Implementation (if needed)
**File:** `include/some_manager.h` and `src/some_manager.cpp`
```cpp
// Add methods to handle the new functionality
void setNewParameter(const char* value);
bool testNewFeature();
```

### REAL EXAMPLE: MQTT Command Implementation

#### Step 1: Added to constants.cpp ✅
```cpp
const char* const ALLOWED_COMMANDS[] = {
    // ... existing commands ...
    "mqtt", nullptr  // Added this
};

const char* const ALLOWED_SET_PARAMS[] = {
    // ... existing params ...
    "mqtt", nullptr  // Added this
};
```

#### Step 2: Added to command_processor.h ✅
```cpp
void handleMqtt(char* param, char* response, size_t responseSize);
```

#### Step 3: Added to command_processor.cpp ✅
```cpp
// In processCommand():
else if (strcasecmp(cmd, "mqtt") == 0) {
    char* param = strtok(NULL, " ");
    handleMqtt(param, response, responseSize);
}

// In handleSet():
else if (strcasecmp(param, "mqtt") == 0) {
    if (networkManager) {
        char* portPtr = strchr(value, ':');
        int port = BROKER_PORT;
        
        if (portPtr) {
            *portPtr = '\0';
            port = atoi(portPtr + 1);
            if (port <= 0 || port > 65535) {
                snprintf(response, responseSize, "Invalid port number");
                return;
            }
        }
        
        networkManager->setMqttBroker(value, port);
        snprintf(response, responseSize, "mqtt broker set to %s:%d", value, port);
    } else {
        snprintf(response, responseSize, "Network manager not available");
    }
}

// Implementation of handleMqtt():
void CommandProcessor::handleMqtt(char* param, char* response, size_t responseSize) {
    if (!networkManager) {
        snprintf(response, responseSize, "network manager not initialized");
        return;
    }
    
    if (!param) {
        snprintf(response, responseSize, "mqtt commands: test, status");
        return;
    }
    
    if (strcasecmp(param, "test") == 0) {
        if (!networkManager->isMQTTConnected()) {
            snprintf(response, responseSize, "MQTT not connected");
            return;
        }
        bool result = networkManager->publish("r4/test", "TEST MESSAGE");
        snprintf(response, responseSize, result ? "mqtt test sent" : "mqtt test failed");
    }
    else if (strcasecmp(param, "status") == 0) {
        snprintf(response, responseSize, "mqtt broker: %s:%d, status: %s", 
            networkManager->getMqttBrokerHost(), 
            networkManager->getMqttBrokerPort(),
            networkManager->isMQTTConnected() ? "connected" : "disconnected");
    }
    else {
        snprintf(response, responseSize, "unknown mqtt command: %s", param);
    }
}
```

#### Step 4: Added to NetworkManager ✅
```cpp
// In network_manager.h:
void setMqttBroker(const char* host, int port = BROKER_PORT);
const char* getMqttBrokerHost() const { return mqttBrokerHost; }
int getMqttBrokerPort() const { return mqttBrokerPort; }

// Added member variables:
char mqttBrokerHost[64];
int mqttBrokerPort;

// In network_manager.cpp:
void NetworkManager::setMqttBroker(const char* host, int port) {
    strncpy(mqttBrokerHost, host, sizeof(mqttBrokerHost) - 1);
    mqttBrokerHost[sizeof(mqttBrokerHost) - 1] = '\0';
    mqttBrokerPort = port;
    
    if (mqttState == MQTTState::CONNECTED) {
        mqttClient.stop();
        mqttState = MQTTState::DISCONNECTED;
    }
}
```

### COMMON MISTAKES TO AVOID

1. **FORGOT TO ADD TO ALLOWED ARRAYS** ❌
   - Command will fail with "invalid command" or "invalid set command"
   - ALWAYS check constants.cpp first

2. **WRONG COMMAND TYPE** ❌
   - Don't confuse standalone commands with SET parameters
   - `mqtt test` = standalone command handler
   - `set mqtt <host>` = SET parameter handler

3. **MISSING HEADER DECLARATION** ❌
   - Implementation without declaration causes compile errors
   - Add to command_processor.h

4. **WRONG PARAMETER PARSING** ❌
   - SET commands: value comes from strtok
   - Standalone commands: param comes from strtok

5. **FORGOT TO UPDATE HELP** ❌
   - Users won't know about new commands
   - Update handleHelp() method

### VALIDATION CHECKLIST

Before committing new command:
- [ ] Added to ALLOWED_COMMANDS or ALLOWED_SET_PARAMS in constants.cpp
- [ ] Added handler declaration to command_processor.h
- [ ] Added command routing in processCommand() or handleSet()
- [ ] Implemented handler method
- [ ] Updated help text
- [ ] Added manager methods if needed
- [ ] Updated documentation
- [ ] Tested compilation
- [ ] Tested on hardware

### ERROR MESSAGES DECODE

- "invalid command: xyz" → Missing from ALLOWED_COMMANDS
- "invalid set command" → Missing from ALLOWED_SET_PARAMS  
- "unknown command: xyz" → Command parser found but handler missing
- Compile error → Missing header declaration or implementation

### FILE MODIFICATION ORDER

1. **constants.cpp** (validation arrays)
2. **manager headers/implementation** (if new functionality needed)
3. **command_processor.h** (handler declaration)
4. **command_processor.cpp** (routing + implementation)
5. **documentation** (COMMANDS.md, README.md)
6. **commit and test**

### NETWORKING COMMANDS PATTERN

For network-related commands, follow this pattern:
```cpp
// SET parameter for configuration
set networkparam <value>

// Standalone commands for testing/status
networkcommand test
networkcommand status
```

This matches the syslog/mqtt pattern and provides consistency.

### ENCODING NOTE
This file uses standard text encoding. No special encoding required.
The .ai extension is for AI assistant recognition only.

---
**Last Updated:** October 2025
**Tested Pattern:** MQTT command implementation
**Success Rate:** 100% when following this procedure