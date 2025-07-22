"""Main plant simulator that orchestrates the production line and MQTT communication."""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from src.config.settings_simple import Settings
from src.core.mqtt_client import MQTTClient
from src.models.production_line import ProductionLine, ProductionOrder


class PlantSimulator:
    """Main simulator for the production plant."""
    
    def __init__(self, settings: Settings, mqtt_client: MQTTClient):
        self.settings = settings
        self.mqtt_client = mqtt_client
        self.logger = logging.getLogger(__name__)
        
        # Initialize production line
        production_config = {
            "name": settings.production_line.name,
            "machines": settings.production_line.machines
        }
        
        self.production_line = ProductionLine(
            production_config, 
            settings.simulation_speed
        )
        
        self.is_running = False
        self.data_publishing_task: Optional[asyncio.Task] = None
        self.order_generation_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the plant simulation."""
        self.logger.info("Starting plant simulator...")
        self.is_running = True
        
        # Start production line
        production_task = asyncio.create_task(self.production_line.start())
        
        # Start data publishing
        self.data_publishing_task = asyncio.create_task(self._publish_data_loop())
        
        # Start automatic order generation
        self.order_generation_task = asyncio.create_task(self._generate_orders_loop())
        
        # Generate initial production order
        await self._generate_initial_order()
        
        self.logger.info("Plant simulator started successfully")
        
        # Wait for production line
        try:
            await production_task
        except asyncio.CancelledError:
            self.logger.info("Production line cancelled")
    
    async def stop(self):
        """Stop the plant simulation."""
        self.logger.info("Stopping plant simulator...")
        self.is_running = False
        
        # Cancel data publishing
        if self.data_publishing_task:
            self.data_publishing_task.cancel()
            try:
                await self.data_publishing_task
            except asyncio.CancelledError:
                pass
        
        # Cancel order generation
        if self.order_generation_task:
            self.order_generation_task.cancel()
            try:
                await self.order_generation_task
            except asyncio.CancelledError:
                pass
        
        # Stop production line
        await self.production_line.stop()
        
        self.logger.info("Plant simulator stopped")
    
    async def _publish_data_loop(self):
        """Continuously publish machine status and production data to MQTT."""
        while self.is_running:
            try:
                # Publish machine status data (includes sensor/actuator data)
                await self._publish_machine_status()
                
                # Publish production status
                await self._publish_production_status()
                
                # Publish alarms and alerts
                await self._publish_alarms()
                
                # Wait before next publication
                await asyncio.sleep(5 / self.settings.simulation_speed)
                
            except Exception as e:
                self.logger.error(f"Error in data publishing loop: {e}")
                await asyncio.sleep(1)
    
    async def _publish_machine_status(self):
        """Publish detailed machine status for each machine."""
        machine_status_data = self.production_line.get_machine_status_data()
        
        for machine_id, machine_status in machine_status_data.items():
            # Publish comprehensive machine status to dedicated topic
            topic_suffix = f"machines/{machine_id}/status"
            await self.mqtt_client.publish_machine_status(
                machine_id=machine_id,
                status_data=machine_status
            )
    
    async def _publish_production_status(self):
        """Publish overall production status."""
        status = self.production_line.get_production_status()
        
        # Add additional production data
        production_data = {
            "production_line_name": status["production_line"],
            "is_running": status["is_running"],
            "shift_info": self._get_shift_info(),
            "current_of": self._get_current_of(),  # OF = Ordem de Fabricação (Production Order)
            "alarm_active": self._check_active_alarms(),
            "line_status": self._get_line_status(),
            "metrics": status["metrics"],
            "machine_count": len(status["machines"]),
            "active_orders": status["active_orders"],
            "active_parts": status["active_parts"],
            "completed_parts": status["completed_parts"]
        }
        
        await self.mqtt_client.publish_production_data(production_data)
    
    async def _publish_alarms(self):
        """Publish active alarms and alerts."""
        alarms = self._generate_alarms()
        
        for alarm in alarms:
            topic_suffix = f"alarms/{alarm['severity']}"
            await self.mqtt_client.publish_production_data(alarm)
    
    def _get_shift_info(self) -> dict:
        """Get current shift information."""
        now = datetime.now()
        hour = now.hour
        
        # Define shifts (can be configured)
        if 6 <= hour < 14:
            shift = "Morning"
            shift_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
        elif 14 <= hour < 22:
            shift = "Afternoon"
            shift_start = now.replace(hour=14, minute=0, second=0, microsecond=0)
        else:
            shift = "Night"
            if hour >= 22:
                shift_start = now.replace(hour=22, minute=0, second=0, microsecond=0)
            else:
                shift_start = (now - timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
        
        shift_duration = timedelta(hours=self.settings.production_line.shift_duration_hours)
        shift_end = shift_start + shift_duration
        time_remaining = shift_end - now
        
        return {
            "current_shift": shift,
            "shift_start": shift_start.isoformat(),
            "shift_end": shift_end.isoformat(),
            "time_remaining_minutes": max(0, time_remaining.total_seconds() / 60),
            "shift_progress_percent": min(100, (now - shift_start).total_seconds() / shift_duration.total_seconds() * 100)
        }
    
    def _get_current_of(self) -> dict:
        """Get current production order (OF) information."""
        if self.production_line.current_orders:
            current_order = self.production_line.current_orders[0]  # Get first active order
            return {
                "of_number": current_order.order_id,
                "part_type": current_order.part_type,
                "total_quantity": current_order.quantity,
                "completed_quantity": current_order.parts_completed,
                "remaining_quantity": current_order.quantity - current_order.parts_completed,
                "progress_percent": (current_order.parts_completed / current_order.quantity) * 100,
                "priority": current_order.priority,
                "status": current_order.status,
                "due_date": current_order.due_date.isoformat() if current_order.due_date else None
            }
        else:
            return {
                "of_number": None,
                "part_type": None,
                "total_quantity": 0,
                "completed_quantity": 0,
                "remaining_quantity": 0,
                "progress_percent": 0,
                "priority": "none",
                "status": "no_active_order",
                "due_date": None
            }
    
    def _check_active_alarms(self) -> bool:
        """Check if there are any active alarms."""
        status = self.production_line.get_production_status()
        
        # Check for machine errors
        for machine_status in status["machines"].values():
            # Handle new structured data format
            machine_state = machine_status.get("machine_production_data", {}).get("state", 
                           machine_status.get("state", "idle"))
            if machine_state in ["error", "malfunction"]:
                return True
        
        # Check for quality issues (only if we've produced parts)
        if status["metrics"]["total_parts_produced"] > 0 and status["metrics"]["quality_rate"] < 0.95:
            return True
        
        # Check for low throughput (only if line has been running for a while)
        if (status["is_running"] and 
            status["metrics"]["total_parts_produced"] > 5 and 
            status["metrics"]["throughput_per_hour"] < 10):
            return True
        
        return False
    
    def _get_line_status(self) -> str:
        """Get overall line status."""
        status = self.production_line.get_production_status()
        
        if not status["is_running"]:
            return "stopped"
        
        # Check if any machine is in error
        for machine_status in status["machines"].values():
            # Handle new structured data format
            machine_state = machine_status.get("machine_production_data", {}).get("state", 
                           machine_status.get("state", "idle"))
            
            if machine_state == "error":
                return "error"
            elif machine_state == "maintenance":
                return "maintenance"
            elif machine_state == "malfunction":
                return "malfunction"
        
        # Check if line is producing
        if status["active_parts"] > 0:
            return "producing"
        elif status["active_orders"] > 0:
            return "waiting"
        else:
            return "idle"
    
    def _generate_alarms(self) -> list:
        """Generate alarm data based on current conditions."""
        alarms = []
        status = self.production_line.get_production_status()
        
        # Machine error alarms
        for machine_id, machine_status in status["machines"].items():
            # Handle new structured data format
            machine_state = machine_status.get("machine_production_data", {}).get("state", 
                           machine_status.get("state", "idle"))
            if machine_state == "error":
                alarms.append({
                    "alarm_id": f"ERROR_{machine_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "machine_id": machine_id,
                    "alarm_type": "machine_error",
                    "severity": "high",
                    "description": f"Machine {machine_id} is in error state",
                    "timestamp": datetime.now().isoformat(),
                    "acknowledged": False
                })
        
        # Quality alarms
        if status["metrics"]["quality_rate"] < 0.95:
            alarms.append({
                "alarm_id": f"QUALITY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "machine_id": None,
                "alarm_type": "quality_issue",
                "severity": "medium",
                "description": f"Quality rate below threshold: {status['metrics']['quality_rate']:.2%}",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            })
        
        # Performance alarms - use throughput instead of OEE
        if status["metrics"]["throughput_per_hour"] < 10:  # Less than 10 parts per hour
            alarms.append({
                "alarm_id": f"PERFORMANCE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "machine_id": None,
                "alarm_type": "performance_issue",
                "severity": "low",
                "description": f"Low throughput: {status['metrics']['throughput_per_hour']:.1f} parts/hour",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            })
        
        return alarms
    
    async def _generate_orders_loop(self):
        """Generate production orders automatically."""
        while self.is_running:
            try:
                # Generate new orders periodically
                if len(self.production_line.current_orders) < 2:  # Keep at least 2 orders in queue
                    await self._generate_random_order()
                
                # Wait before checking again
                await asyncio.sleep(300 / self.settings.simulation_speed)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in order generation loop: {e}")
                await asyncio.sleep(30)
    
    async def _generate_initial_order(self):
        """Generate an initial production order to start the simulation."""
        order = ProductionOrder(
            order_id=f"OF_{datetime.now().strftime('%Y%m%d')}001",
            part_type="Widget_A",
            quantity=50,
            priority="normal",
            due_date=datetime.now() + timedelta(hours=4)
        )
        
        await self.production_line.add_production_order(order)
        self.logger.info(f"Generated initial production order: {order.order_id}")
    
    async def _generate_random_order(self):
        """Generate a random production order."""
        order_number = random.randint(1, 999)
        part_types = ["Widget_A", "Widget_B", "Component_X", "Assembly_Y"]
        priorities = ["low", "normal", "high"]
        
        order = ProductionOrder(
            order_id=f"OF_{datetime.now().strftime('%Y%m%d')}{order_number:03d}",
            part_type=random.choice(part_types),
            quantity=random.randint(20, 100),
            priority=random.choice(priorities),
            due_date=datetime.now() + timedelta(hours=random.randint(2, 8))
        )
        
        await self.production_line.add_production_order(order)
        self.logger.info(f"Generated new production order: {order.order_id}")
