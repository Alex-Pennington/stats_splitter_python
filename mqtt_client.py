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
        """Handle a single MQTT message from LogSplitter Controller"""
        topic = str(message.topic)
        payload = message.payload.decode().strip()
        
        logger.debug(f"Received message on topic '{topic}': {payload}")
        
        try:
            # Handle LogSplitter Controller sequence events
            if topic == 'controller/sequence/event':
                await self._handle_sequence_event(payload)
                
            # Handle sequence state changes
            elif topic == 'controller/sequence/state':
                await self._handle_sequence_state(payload)
                
            # Handle sequence status (active/inactive)
            elif topic == 'controller/sequence/active':
                await self._handle_sequence_active(payload)
                
            # Handle sequence stage tracking
            elif topic == 'controller/sequence/stage':
                await self._handle_sequence_stage(payload)
                
            # Handle pressure readings
            elif topic == 'controller/pressure/hydraulic_system':
                await self._handle_pressure_reading(payload, 'hydraulic_system')
            elif topic == 'controller/pressure/hydraulic_filter':
                await self._handle_pressure_reading(payload, 'hydraulic_filter')
            elif topic == 'controller/pressure':  # backward compatibility
                await self._handle_pressure_reading(payload, 'hydraulic')
                
            # Handle safety system status
            elif topic == 'controller/safety/active':
                await self._handle_safety_status(payload)
            elif topic == 'controller/safety/estop':
                await self._handle_emergency_stop(payload)
            elif topic == 'controller/safety/engine':
                await self._handle_engine_status(payload)
                
            # Handle relay states (hydraulic valve control)
            elif topic.startswith('controller/relays/') and topic.endswith('/state'):
                relay_num = topic.split('/')[-2]
                await self._handle_relay_state(relay_num, payload)
                
            # Handle input pin changes (limit switches, buttons)
            elif topic.startswith('controller/inputs/') and topic.endswith('/state'):
                pin_num = topic.split('/')[-2]
                await self._handle_input_state(pin_num, payload)
                
            # Handle fuel level monitoring
            elif topic == 'monitor/fuel/gallons':
                await self._handle_fuel_level(payload)
                
            # Handle command responses
            elif topic == 'controller/control/resp':
                logger.info(f"Controller response: {payload}")
                
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
                                    logger.debug(f"General stat: {topic}/{key} = {value}")
                        elif isinstance(data, (int, float)):
                            logger.debug(f"General stat: {topic} = {data}")
                    else:
                        # Try to parse as plain number for general statistics
                        try:
                            value = float(payload)
                            logger.debug(f"General stat: {topic} = {value}")
                        except ValueError:
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
    
    async def _handle_sequence_event(self, payload):
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
    
    async def _handle_sequence_state(self, payload):
        """Handle sequence state changes"""
        logger.info(f"Sequence state: {payload}")
        
        if payload == 'start':
            self.production_stats.handle_sequence_event('cycle_start')
        elif payload == 'complete':
            self.production_stats.handle_sequence_event('cycle_complete')
        elif payload in ['stopped', 'abort']:
            self.production_stats.handle_sequence_event('abort')
    
    async def _handle_sequence_active(self, payload):
        """Handle sequence active status"""
        is_active = payload in ['1', 'true', 'True']
        logger.debug(f"Sequence active: {is_active}")
        
        if is_active:
            self.production_stats.handle_sequence_event('sequence_start')
        else:
            self.production_stats.handle_sequence_event('sequence_end')
    
    async def _handle_sequence_stage(self, payload):
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
    
    async def _handle_pressure_reading(self, payload, sensor_type):
        """Handle pressure sensor readings"""
        try:
            pressure_value = float(payload)
            self.production_stats.handle_pressure_reading(pressure_value, sensor_type)
        except ValueError:
            logger.warning(f"Could not parse pressure value: {payload}")
    
    async def _handle_safety_status(self, payload):
        """Handle safety system status"""
        is_active = payload in ['1', 'true', 'True']
        logger.info(f"Safety system active: {is_active}")
        
        if is_active:
            self.production_stats.handle_sequence_event('safety_stop')
    
    async def _handle_emergency_stop(self, payload):
        """Handle emergency stop button status"""
        is_pressed = payload in ['1', 'true', 'True']
        logger.info(f"Emergency stop pressed: {is_pressed}")
        
        if is_pressed:
            self.production_stats.handle_sequence_event('emergency_stop')
    
    async def _handle_engine_status(self, payload):
        """Handle engine status"""
        logger.info(f"Engine status: {payload}")
        # Could track engine running time for fuel calculations
    
    async def _handle_relay_state(self, relay_num, payload):
        """Handle relay state changes"""
        is_on = payload in ['1', 'true', 'True']
        logger.debug(f"Relay {relay_num} state: {'ON' if is_on else 'OFF'}")
        
        # Track hydraulic valve operations
        if relay_num == '1' and is_on:  # Extend valve activated
            self.production_stats.handle_sequence_event('extend_valve_on')
        elif relay_num == '2' and is_on:  # Retract valve activated
            self.production_stats.handle_sequence_event('retract_valve_on')
    
    async def _handle_input_state(self, pin_num, payload):
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
    
    async def _handle_fuel_level(self, payload):
        """Handle fuel level readings from monitor/fuel/gallons"""
        try:
            fuel_level = float(payload)
            logger.debug(f"Fuel level: {fuel_level} gallons")
            self.production_stats.handle_fuel_level(fuel_level)
        except ValueError:
            logger.warning(f"Invalid fuel level reading: {payload}")
    
    def stop(self):
        """Stop the MQTT client"""
        logger.info("Stopping MQTT client...")
        self.is_running = False