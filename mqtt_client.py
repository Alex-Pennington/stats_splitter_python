import asyncio
import logging
import json
from aiomqtt import Client
from typing import Dict, List, Callable
from production_stats import ProductionStatsEngine

logger = logging.getLogger(__name__)

class MQTTProductionClient:
    """MQTT client specialized for firewood splitter production monitoring"""
    
    def __init__(self, config, production_stats: ProductionStatsEngine):
        self.config = config
        self.production_stats = production_stats
        self.client = None
        self.is_running = False
        
    async def start(self):
        """Start the MQTT client and begin subscribing to topics"""
        logger.info(f"Connecting to MQTT broker at {self.config.mqtt_host}:{self.config.mqtt_port}")
        
        try:
            async with Client(
                hostname=self.config.mqtt_host,
                port=self.config.mqtt_port,
                username=self.config.mqtt_username,
                password=self.config.mqtt_password
            ) as client:
                self.client = client
                self.is_running = True
                
                # Subscribe to all configured topics
                await self._subscribe_to_topics()
                
                # Start message processing loop
                await self._process_messages()
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            raise
    
    async def _subscribe_to_topics(self):
        """Subscribe to all topics defined in configuration"""
        for topic in self.config.mqtt_topics:
            logger.info(f"Subscribing to topic: {topic}")
            await self.client.subscribe(topic)
    
    async def _process_messages(self):
        """Process incoming MQTT messages"""
        logger.info("Starting MQTT message processing loop...")
        
        async with self.client.messages() as messages:
            async for message in messages:
                try:
                    await self._handle_message(message)
                except Exception as e:
                    logger.error(f"Error processing message from {message.topic}: {e}")
    
    async def _handle_message(self, message):
        """Handle a single MQTT message for production monitoring"""
        topic = str(message.topic)
        payload = message.payload.decode().strip()
        
        logger.debug(f"Received message on topic '{topic}': {payload}")
        
        try:
            # Handle sequence events
            if topic.endswith('/sequence/event'):
                self.production_stats.handle_sequence_event(payload)
                
            # Handle sequence status
            elif topic.endswith('/sequence/status'):
                self.production_stats.handle_sequence_status(payload)
                
            # Handle basket exchange signals
            elif topic.endswith('/signals/basket_exchange'):
                # Payload might be "1" for exchange signal
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
                    
            # Handle input pin changes (for operator signals)
            elif '/inputs/' in topic:
                try:
                    # Extract pin number from topic like "controller/inputs/8"
                    pin_number = topic.split('/')[-1]
                    pin_state = int(payload) if payload.isdigit() else payload
                    logger.info(f"Input pin {pin_number} changed to {pin_state}")
                    
                    # Pin 8 is typically the splitter operator signal
                    if pin_number == '8' and pin_state in [1, '1', 'ON', 'HIGH']:
                        logger.info("Operator signal detected")
                        
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse input pin data: {topic} = {payload}")
                    
            # Handle other numeric data for general statistics
            else:
                try:
                    # Try to parse as JSON first
                    if payload.startswith('{') or payload.startswith('['):
                        data = json.loads(payload)
                        if isinstance(data, dict):
                            # Handle JSON object with multiple values
                            for key, value in data.items():
                                if isinstance(value, (int, float)):
                                    # Store as general topic statistics
                                    logger.debug(f"General stat: {topic}/{key} = {value}")
                        elif isinstance(data, (int, float)):
                            # Handle JSON number
                            logger.debug(f"General stat: {topic} = {data}")
                    else:
                        # Try to parse as plain number for general statistics
                        try:
                            value = float(payload)
                            logger.debug(f"General stat: {topic} = {value}")
                        except ValueError:
                            # Non-numeric payload, just log it
                            logger.debug(f"Non-numeric message: {topic} = {payload}")
                            
                except json.JSONDecodeError:
                    # Non-JSON payload, try as number
                    try:
                        value = float(payload)
                        logger.debug(f"General stat: {topic} = {value}")
                    except ValueError:
                        logger.debug(f"Text message: {topic} = {payload}")
                        
        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")
            logger.error(f"Payload was: {payload}")
    
    def stop(self):
        """Stop the MQTT client"""
        logger.info("Stopping MQTT client...")
        self.is_running = False