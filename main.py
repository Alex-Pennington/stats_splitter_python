import asyncio
import logging
from mqtt_client import MQTTProductionClient
from web_server import create_app
from production_stats import ProductionStatsEngine
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    logger.info("Starting stats_splitter_python application...")
    
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
    mqtt_client = MQTTProductionClient(config, production_stats)
    
    # Create Flask app
    app = create_app(production_stats)
    
    # Start MQTT client in background
    mqtt_task = asyncio.create_task(mqtt_client.start())
    
    # Start Flask web server in a separate thread
    import threading
    def run_flask():
        logger.info(f"Starting web server on port {config.web_port}")
        app.run(host='0.0.0.0', port=config.web_port, debug=config.debug, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for MQTT task to complete (this should run indefinitely)
    try:
        await mqtt_task
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    # Fix for Windows asyncio compatibility
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise