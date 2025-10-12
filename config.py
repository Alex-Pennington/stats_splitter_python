import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for the MQTT stats application"""
    
    def __init__(self):
        # MQTT Configuration
        self.mqtt_host = os.getenv('MQTT_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', None)
        self.mqtt_password = os.getenv('MQTT_PASSWORD', None)
        
        # MQTT Topics - can be comma-separated list in env var
        topics_env = os.getenv('MQTT_TOPICS', 'sensor/+,home/+/temperature,stats/+')
        self.mqtt_topics = [topic.strip() for topic in topics_env.split(',') if topic.strip()]
        
        # Web Server Configuration
        self.web_port = int(os.getenv('WEB_PORT', '5000'))
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Application Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
    def validate(self):
        """Validate configuration and return any errors"""
        errors = []
        
        if not self.mqtt_host:
            errors.append("MQTT_HOST is required")
        
        if not self.mqtt_topics:
            errors.append("At least one MQTT topic must be configured")
        
        if self.mqtt_port < 1 or self.mqtt_port > 65535:
            errors.append("MQTT_PORT must be between 1 and 65535")
            
        if self.web_port < 1 or self.web_port > 65535:
            errors.append("WEB_PORT must be between 1 and 65535")
        
        return errors
    
    def __str__(self):
        """String representation of configuration (without sensitive data)"""
        return f"""Configuration:
  MQTT Host: {self.mqtt_host}:{self.mqtt_port}
  MQTT Username: {'***' if self.mqtt_username else 'None'}
  MQTT Topics: {', '.join(self.mqtt_topics)}
  Web Port: {self.web_port}
  Debug Mode: {self.debug}
  Log Level: {self.log_level}
"""