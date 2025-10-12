#!/usr/bin/env python3
"""
Windows-compatible version of the main application
Uses synchronous MQTT client to avoid Windows asyncio issues
"""

import time
import threading
import logging
import signal
import sys
from web_server import create_app
from production_stats import ProductionStatsEngine
from config import Config
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WindowsMQTTClient:
    """Windows-compatible MQTT client using paho-mqtt directly"""
    
    def __init__(self, config, production_stats):
        self.config = config
        self.production_stats = production_stats
        self.client = None
        self.connected = False
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.connected = True
            # Subscribe to all configured topics
            for topic in self.config.mqtt_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects"""
        logger.warning(f"Disconnected from MQTT broker, return code {rc}")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from LogSplitter Controller"""
        try:
            topic = str(msg.topic)
            payload = msg.payload.decode().strip()
            
            logger.debug(f"Received message on topic '{topic}': {payload}")
            
            # Handle LogSplitter Controller sequence events
            if topic == 'controller/sequence/event':
                self._handle_sequence_event(payload)
                
            # Handle sequence state changes
            elif topic == 'controller/sequence/state':
                self._handle_sequence_state(payload)
                
            # Handle sequence status (active/inactive)
            elif topic == 'controller/sequence/active':
                self._handle_sequence_active(payload)
                
            # Handle sequence stage tracking
            elif topic == 'controller/sequence/stage':
                self._handle_sequence_stage(payload)
                
            # Handle pressure readings
            elif topic == 'controller/pressure/hydraulic_system':
                self._handle_pressure_reading(payload, 'hydraulic_system')
            elif topic == 'controller/pressure/hydraulic_filter':
                self._handle_pressure_reading(payload, 'hydraulic_filter')
            elif topic == 'controller/pressure':  # backward compatibility
                self._handle_pressure_reading(payload, 'hydraulic')
                
            # Handle safety system status
            elif topic == 'controller/safety/active':
                self._handle_safety_status(payload)
            elif topic == 'controller/safety/estop':
                self._handle_emergency_stop(payload)
            elif topic == 'controller/safety/engine':
                self._handle_engine_status(payload)
                
            # Handle relay states (hydraulic valve control)
            elif topic.startswith('controller/relays/') and topic.endswith('/state'):
                relay_num = topic.split('/')[-2]
                self._handle_relay_state(relay_num, payload)
                
            # Handle input pin changes (limit switches, buttons)
            elif topic.startswith('controller/inputs/') and topic.endswith('/state'):
                pin_num = topic.split('/')[-2]
                self._handle_input_state(pin_num, payload)
                
            # Handle fuel level monitoring
            elif topic == 'monitor/fuel/gallons':
                self._handle_fuel_level(payload)
                
            # Handle command responses
            elif topic == 'controller/control/resp':
                logger.info(f"Controller response: {payload}")
                
        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")
    
    def _handle_sequence_event(self, payload):
        """Handle sequence event messages"""
        logger.info(f"Sequence event: {payload}")
        
        # Map controller events to production events
        if payload in ['started_R1', 'manual_extend_started']:
            self.production_stats.handle_sequence_event('extend_start')
        elif payload in ['switched_to_R2_pressure_or_limit']:
            self.production_stats.handle_sequence_event('extend_complete')
        elif payload in ['complete_pressure_or_limit', 'manual_extend_limit_reached']:
            self.production_stats.handle_sequence_event('cycle_complete')
        elif payload == 'abort':
            self.production_stats.handle_sequence_event('abort')
    
    def _handle_sequence_state(self, payload):
        """Handle sequence state changes"""
        logger.info(f"Sequence state: {payload}")
        
        if payload == 'start':
            self.production_stats.handle_sequence_event('cycle_start')
        elif payload == 'complete':
            self.production_stats.handle_sequence_event('cycle_complete')
        elif payload in ['stopped', 'abort']:
            self.production_stats.handle_sequence_event('abort')
    
    def _handle_sequence_active(self, payload):
        """Handle sequence active status"""
        is_active = payload in ['1', 'true', 'True']
        logger.debug(f"Sequence active: {is_active}")
        
        if is_active:
            self.production_stats.handle_sequence_event('sequence_start')
        else:
            self.production_stats.handle_sequence_event('sequence_end')
    
    def _handle_sequence_stage(self, payload):
        """Handle sequence stage tracking"""
        try:
            stage = int(payload)
            logger.debug(f"Sequence stage: {stage}")
            # Stage 0 = idle, 1+ = active stages
            if stage == 1:
                self.production_stats.handle_sequence_event('extend_start')
            elif stage == 2:
                self.production_stats.handle_sequence_event('retract_start')
        except ValueError:
            logger.warning(f"Could not parse sequence stage: {payload}")
    
    def _handle_pressure_reading(self, payload, sensor_type):
        """Handle pressure sensor readings"""
        try:
            pressure_value = float(payload)
            self.production_stats.handle_pressure_reading(pressure_value, sensor_type)
        except ValueError:
            logger.warning(f"Could not parse pressure value: {payload}")
    
    def _handle_safety_status(self, payload):
        """Handle safety system status"""
        is_active = payload in ['1', 'true', 'True']
        logger.info(f"Safety system active: {is_active}")
        
        if is_active:
            self.production_stats.handle_sequence_event('safety_stop')
    
    def _handle_emergency_stop(self, payload):
        """Handle emergency stop button status"""
        is_pressed = payload in ['1', 'true', 'True']
        logger.info(f"Emergency stop pressed: {is_pressed}")
        
        if is_pressed:
            self.production_stats.handle_sequence_event('emergency_stop')
    
    def _handle_engine_status(self, payload):
        """Handle engine status"""
        logger.info(f"Engine status: {payload}")
        # Could track engine running time for fuel calculations
    
    def _handle_relay_state(self, relay_num, payload):
        """Handle relay state changes"""
        is_on = payload in ['1', 'true', 'True']
        logger.debug(f"Relay {relay_num} state: {'ON' if is_on else 'OFF'}")
        
        # Track hydraulic valve operations
        if relay_num == '1' and is_on:  # Extend valve activated
            self.production_stats.handle_sequence_event('extend_valve_on')
        elif relay_num == '2' and is_on:  # Retract valve activated
            self.production_stats.handle_sequence_event('retract_valve_on')
    
    def _handle_input_state(self, pin_num, payload):
        """Handle input pin state changes"""
        is_active = payload in ['1', 'true', 'True']
        logger.debug(f"Input pin {pin_num} state: {'ACTIVE' if is_active else 'INACTIVE'}")
        
        # Track limit switch activations
        if pin_num == '6' and is_active:  # Extend limit switch
            self.production_stats.handle_sequence_event('extend_limit_reached')
        elif pin_num == '7' and is_active:  # Retract limit switch
            self.production_stats.handle_sequence_event('retract_limit_reached')
        elif pin_num == '4' and is_active:  # Safety clear button
            self.production_stats.handle_sequence_event('safety_clear')
    
    def _handle_fuel_level(self, payload):
        """Handle fuel level readings from monitor/fuel/gallons"""
        try:
            fuel_level = float(payload)
            logger.debug(f"Fuel level: {fuel_level} gallons")
            self.production_stats.handle_fuel_level(fuel_level)
        except ValueError:
            logger.warning(f"Invalid fuel level reading: {payload}")
    
    def start(self):
        """Start the MQTT client"""
        try:
            self.client = mqtt.Client()
            
            # Set credentials if provided
            if self.config.mqtt_username and self.config.mqtt_password:
                self.client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
                logger.info(f"Using MQTT credentials for user: {self.config.mqtt_username}")
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {self.config.mqtt_host}:{self.config.mqtt_port}")
            self.client.connect(self.config.mqtt_host, self.config.mqtt_port, 60)
            
            # Start the network loop
            self.client.loop_start()
            self.running = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            return False
    
    def stop(self):
        """Stop the MQTT client"""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")

def main():
    """Main application entry point"""
    logger.info("Starting Windows-compatible stats_splitter_python application...")
    
    # Load configuration
    config = Config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return
    
    logger.info(str(config))
    
    # Initialize production statistics engine
    production_stats = ProductionStatsEngine()
    
    # Initialize MQTT client
    mqtt_client = WindowsMQTTClient(config, production_stats)
    
    # Start MQTT client
    if not mqtt_client.start():
        logger.error("Failed to start MQTT client")
        return
    
    # Create Flask app
    app = create_app(production_stats)
    
    # Start Flask web server in a separate thread
    def run_flask():
        logger.info(f"Starting web server on port {config.web_port}")
        app.run(host='0.0.0.0', port=config.web_port, debug=config.debug, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping...")
        mqtt_client.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main loop - keep the application running
    try:
        logger.info("🪓 Firewood Splitter Statistics System is running!")
        logger.info(f"📊 Web dashboard available at: http://localhost:{config.web_port}")
        logger.info("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        mqtt_client.stop()

if __name__ == "__main__":
    main()