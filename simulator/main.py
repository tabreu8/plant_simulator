"""
Production Line Simulator

A configurable simulation of industrial production lines with MQTT communication.
Simulates sensors, actuators, and production data for realistic manufacturing scenarios.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from src.config.settings_simple import Settings
from src.core.plant_simulator import PlantSimulator
from src.core.mqtt_client import MQTTClient


class ProductionLineSimulator:
    """Main application class for the production line simulator."""
    
    def __init__(self):
        self.settings = Settings()
        self.mqtt_client: Optional[MQTTClient] = None
        self.plant_simulator: Optional[PlantSimulator] = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the production line simulation."""
        try:
            self.logger.info("Starting Production Line Simulator...")
            
            # Initialize MQTT client
            self.mqtt_client = MQTTClient(self.settings)
            await self.mqtt_client.connect()
            
            # Initialize plant simulator
            self.plant_simulator = PlantSimulator(self.settings, self.mqtt_client)
            
            # Start simulation
            self.running = True
            await self.plant_simulator.start()
            
            self.logger.info("Production Line Simulator started successfully")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error starting simulator: {e}")
            raise
    
    async def stop(self):
        """Stop the production line simulation."""
        self.logger.info("Stopping Production Line Simulator...")
        self.running = False
        
        if self.plant_simulator:
            await self.plant_simulator.stop()
        
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
        
        self.logger.info("Production Line Simulator stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point."""
    simulator = ProductionLineSimulator()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, simulator.signal_handler)
    signal.signal(signal.SIGTERM, simulator.signal_handler)
    
    try:
        await simulator.start()
    except KeyboardInterrupt:
        await simulator.stop()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
