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
        """Callback for when a message is received"""
        try:
            topic = str(msg.topic)
            payload = msg.payload.decode().strip()
            
            logger.debug(f"Received message on topic '{topic}': {payload}")
            
            # Handle sequence events
            if topic.endswith('/sequence/event'):
                self.production_stats.handle_sequence_event(payload)
                
            # Handle sequence status
            elif topic.endswith('/sequence/status'):
                self.production_stats.handle_sequence_status(payload)
                
            # Handle basket exchange signals
            elif topic.endswith('/signals/basket_exchange'):
                if payload in ['1', 'true', 'True', 'exchange']:
                    self.production_stats.handle_basket_exchange()
                    
            # Handle pressure readings
            elif '/pressure/' in topic:
                try:
                    pressure_value = float(payload)
                    if 'hydraulic_system' in topic:
                        self.production_stats.handle_pressure_reading(pressure_value, 'hydraulic_system')
                    elif 'hydraulic_filter' in topic:
                        self.production_stats.handle_pressure_reading(pressure_value, 'hydraulic_filter')
                    elif topic.endswith('/pressure'):  # backward compatibility
                        self.production_stats.handle_pressure_reading(pressure_value, 'hydraulic')
                except ValueError:
                    logger.warning(f"Could not parse pressure value: {payload}")
                    
            # Handle fuel level
            elif topic.endswith('/fuel_level'):
                try:
                    fuel_level = float(payload)
                    self.production_stats.handle_fuel_level(fuel_level)
                except ValueError:
                    logger.warning(f"Could not parse fuel level: {payload}")
                    
            # Handle input pin changes
            elif '/inputs/' in topic:
                try:
                    pin_number = topic.split('/')[-1]
                    pin_state = int(payload) if payload.isdigit() else payload
                    logger.info(f"Input pin {pin_number} changed to {pin_state}")
                    
                    # Pin 8 is typically the splitter operator signal
                    if pin_number == '8' and pin_state in [1, '1', 'ON', 'HIGH']:
                        logger.info("Operator signal detected")
                        
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse input pin data: {topic} = {payload}")
                    
        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")
    
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