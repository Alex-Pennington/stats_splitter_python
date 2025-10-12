#!/usr/bin/env python3
"""
Production MQTT Monitor for LogSplitter Controller
Connects to the production MQTT server and displays real-time messages
"""

import paho.mqtt.client as mqtt
import time
import logging
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMQTTMonitor:
    """Monitor production MQTT messages from LogSplitter Controller"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.connected = False
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info(f"✅ Connected to production MQTT broker: {self.config.mqtt_host}:{self.config.mqtt_port}")
            self.connected = True
            
            # Subscribe to all controller topics
            topics_to_subscribe = [
                "controller/+",
                "controller/+/+", 
                "controller/+/+/+"
            ]
            
            for topic in topics_to_subscribe:
                client.subscribe(topic)
                logger.info(f"📡 Subscribed to: {topic}")
                
        else:
            logger.error(f"❌ Failed to connect, return code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.warning(f"🔌 Disconnected from MQTT broker, return code {rc}")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback for received messages"""
        self.message_count += 1
        topic = str(msg.topic)
        payload = msg.payload.decode().strip()
        
        # Color code different message types
        if 'sequence' in topic:
            logger.info(f"🔄 [{self.message_count:04d}] SEQUENCE: {topic} = {payload}")
        elif 'pressure' in topic:
            logger.info(f"📊 [{self.message_count:04d}] PRESSURE: {topic} = {payload}")
        elif 'safety' in topic:
            logger.info(f"⚠️  [{self.message_count:04d}] SAFETY: {topic} = {payload}")
        elif 'relays' in topic:
            logger.info(f"🔧 [{self.message_count:04d}] RELAY: {topic} = {payload}")
        elif 'inputs' in topic:
            logger.info(f"🎛️  [{self.message_count:04d}] INPUT: {topic} = {payload}")
        elif 'control' in topic:
            logger.info(f"💬 [{self.message_count:04d}] CONTROL: {topic} = {payload}")
        else:
            logger.info(f"📨 [{self.message_count:04d}] OTHER: {topic} = {payload}")
    
    def start_monitoring(self, duration_minutes=5):
        """Start monitoring production MQTT messages"""
        try:
            # Validate configuration
            errors = self.config.validate()
            if errors:
                logger.error("Configuration errors:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # Create MQTT client
            self.client = mqtt.Client()
            
            # Set credentials
            if self.config.mqtt_username and self.config.mqtt_password:
                self.client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
                logger.info(f"🔐 Using credentials for user: {self.config.mqtt_username}")
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Connect to broker
            logger.info(f"🌐 Connecting to production MQTT broker...")
            self.client.connect(self.config.mqtt_host, self.config.mqtt_port, 60)
            
            # Start network loop
            self.client.loop_start()
            
            # Monitor for specified duration
            logger.info(f"🔍 Monitoring LogSplitter Controller for {duration_minutes} minutes...")
            logger.info("Press Ctrl+C to stop monitoring early")
            
            start_time = time.time()
            try:
                while time.time() - start_time < duration_minutes * 60:
                    time.sleep(1)
                    
                    # Show periodic status
                    elapsed_minutes = (time.time() - start_time) / 60
                    if int(elapsed_minutes) % 1 == 0 and elapsed_minutes > 0:
                        logger.info(f"⏱️  Monitoring: {elapsed_minutes:.1f}min elapsed, {self.message_count} messages received")
                        
            except KeyboardInterrupt:
                logger.info("⏹️  Monitoring stopped by user")
            
            # Stop and cleanup
            self.client.loop_stop()
            self.client.disconnect()
            
            logger.info(f"📈 Monitoring complete: {self.message_count} total messages received")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}")
            return False

def main():
    """Main entry point"""
    logger.info("🪓 LogSplitter Controller Production MQTT Monitor")
    logger.info("=" * 60)
    
    monitor = ProductionMQTTMonitor()
    
    # Monitor for 5 minutes by default
    success = monitor.start_monitoring(duration_minutes=5)
    
    if success:
        logger.info("✅ Production MQTT monitoring completed successfully")
    else:
        logger.error("❌ Production MQTT monitoring failed")

if __name__ == "__main__":
    main()