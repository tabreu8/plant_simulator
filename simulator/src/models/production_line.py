"""Production line model for orchestrating multiple machines."""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.models.machine import Machine, ProductionPart, MachineState


@dataclass
class ProductionOrder:
    """Represents a production order."""
    order_id: str
    part_type: str
    quantity: int
    priority: str = "normal"  # low, normal, high, urgent
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    parts_released: int = 0
    parts_completed: int = 0
    status: str = "pending"  # pending, in_progress, completed, cancelled


@dataclass
class ProductionMetrics:
    """Production line performance metrics."""
    total_parts_produced: int = 0
    total_parts_rejected: int = 0
    total_downtime: timedelta = field(default_factory=lambda: timedelta())
    cycle_time_avg: float = 0.0
    throughput_per_hour: float = 0.0
    quality_rate: float = 0.0


class ProductionLine:
    """Represents a complete production line with multiple machines."""
    
    def __init__(self, config: Dict[str, Any], simulation_speed: float = 1.0):
        self.config = config
        self.name = config["name"]
        self.simulation_speed = simulation_speed
        
        # Initialize machines
        self.machines: Dict[str, Machine] = {}
        for machine_config in config["machines"]:
            machine = Machine(machine_config, simulation_speed)
            self.machines[machine.id] = machine
        
        # Production state
        self.is_running = False
        self.current_orders: List[ProductionOrder] = []
        self.active_parts: List[ProductionPart] = []
        self.completed_parts: List[ProductionPart] = []
        
        # Inter-station buffers for realistic flow
        self.station_buffers: Dict[str, List[ProductionPart]] = {}
        for machine_id in self.machines.keys():
            self.station_buffers[f"{machine_id}_input"] = []
            self.station_buffers[f"{machine_id}_output"] = []
        
        # Performance tracking
        self.metrics = ProductionMetrics()
        self.start_time: Optional[datetime] = None
        
        # Production flow configuration - maintain order
        self.machine_sequence = list(self.machines.keys())
        
        # Flow control settings
        self.max_buffer_size = 2  # Maximum parts waiting between stations
        self.min_cycle_time = 5.0  # Minimum time between part releases
        self.last_part_release = datetime.now()
        
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    async def start(self):
        """Start the production line."""
        self.logger.info(f"Starting production line: {self.name}")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start all machines
        for machine in self.machines.values():
            await machine.start()
        
        # Start production tasks - simplified to just the scheduler
        tasks = [
            asyncio.create_task(self._production_scheduler()),
            asyncio.create_task(self._metrics_collector())
        ]
        
        self.logger.info("Production line started successfully")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("Production tasks cancelled")
    
    async def stop(self):
        """Stop the production line."""
        self.logger.info(f"Stopping production line: {self.name}")
        self.is_running = False
        
        # Stop all machines
        for machine in self.machines.values():
            await machine.stop()
        
        self.logger.info("Production line stopped")
    
    async def add_production_order(self, order: ProductionOrder):
        """Add a new production order."""
        self.logger.info(f"Adding production order: {order.order_id} for {order.quantity} {order.part_type}")
        self.current_orders.append(order)
        order.status = "in_progress"
    
    async def _production_scheduler(self):
        """Schedule production based on orders with realistic flow control."""
        while self.is_running:
            try:
                # Check if we can release a new part to the line
                await self._try_release_new_part()
                
                # Move parts through the production line
                await self._manage_part_flow()
                
                # Process parts at each station
                await self._process_station_queues()
                
                # Clean up completed orders
                await self._update_order_status()
                
                await asyncio.sleep(1 / self.simulation_speed)  # Check every second for responsiveness
                
            except Exception as e:
                self.logger.error(f"Error in production scheduler: {e}")
                await asyncio.sleep(1)
    
    async def _try_release_new_part(self):
        """Try to release a new part to the first station if conditions allow."""
        # Check timing constraints
        time_since_last = (datetime.now() - self.last_part_release).total_seconds()
        if time_since_last < self.min_cycle_time / self.simulation_speed:
            return
        
        # Check if first station input buffer has space
        first_station = self.machine_sequence[0]
        input_buffer = self.station_buffers[f"{first_station}_input"]
        
        if len(input_buffer) >= self.max_buffer_size:
            return  # Line is backed up
        
        # Find order that needs parts
        for order in self.current_orders:
            if order.status == "in_progress" and order.parts_released < order.quantity:
                # Create new part
                order.parts_released += 1
                part_id = f"{order.order_id}_{order.parts_released:04d}"
                part = ProductionPart(
                    part_id=part_id,
                    part_type=order.part_type,
                    created_at=datetime.now()
                )
                
                # Add to first station input buffer
                input_buffer.append(part)
                self.active_parts.append(part)
                self.last_part_release = datetime.now()
                
                self.logger.info(f"Released new part {part_id} to production line")
                break
    
    async def _manage_part_flow(self):
        """Manage flow of parts between stations."""
        # Process each station's output buffer
        for i, machine_id in enumerate(self.machine_sequence):
            output_buffer = self.station_buffers[f"{machine_id}_output"]
            
            # Move completed parts to next station or completion
            parts_to_move = output_buffer.copy()
            for part in parts_to_move:
                if i + 1 < len(self.machine_sequence):
                    # Move to next station
                    next_machine_id = self.machine_sequence[i + 1]
                    next_input_buffer = self.station_buffers[f"{next_machine_id}_input"]
                    
                    # Check if next station has space
                    if len(next_input_buffer) < self.max_buffer_size:
                        output_buffer.remove(part)
                        next_input_buffer.append(part)
                        self.logger.info(f"Part {part.part_id} moved from {machine_id} to {next_machine_id} buffer")
                else:
                    # Part completed all stations
                    output_buffer.remove(part)
                    await self._complete_part(part)
    
    async def _process_station_queues(self):
        """Process parts waiting at each station."""
        for machine_id in self.machine_sequence:
            machine = self.machines[machine_id]
            input_buffer = self.station_buffers[f"{machine_id}_input"]
            output_buffer = self.station_buffers[f"{machine_id}_output"]
            
            # If machine is idle and has parts waiting
            if machine.state == MachineState.IDLE and input_buffer:
                part = input_buffer.pop(0)  # Take first part (FIFO)
                
                self.logger.info(f"Starting processing of part {part.part_id} at {machine_id}")
                
                # Process part (this will block until complete)
                try:
                    processed_part = await machine.process_part(part)
                    output_buffer.append(processed_part)
                    self.logger.info(f"Part {part.part_id} completed processing at {machine_id}")
                except Exception as e:
                    self.logger.error(f"Error processing part {part.part_id} at {machine_id}: {e}")
    
    async def _update_order_status(self):
        """Update order completion status."""
        for order in self.current_orders[:]:
            completed_count = len([p for p in self.completed_parts 
                                 if p.part_id.startswith(order.order_id)])
            order.parts_completed = completed_count
            
            if order.parts_completed >= order.quantity:
                order.status = "completed"
                self.logger.info(f"Production order {order.order_id} completed")
                self.current_orders.remove(order)
    
    async def _complete_part(self, part: ProductionPart):
        """Complete processing of a part."""
        self.logger.info(f"Part {part.part_id} completed entire production line")
        
        # Remove from active parts
        if part in self.active_parts:
            self.active_parts.remove(part)
        
        # Add to completed parts
        self.completed_parts.append(part)
        
        # Update metrics based on part quality
        self.metrics.total_parts_produced += 1
        
        # Track rejected parts
        if part.quality_status in ["fail", "reject", "error"]:
            self.metrics.total_parts_rejected += 1
        
        # Update order progress
        for order in self.current_orders:
            if part.part_id.startswith(order.order_id):
                order.parts_completed += 1
                break
    
    def get_buffer_status(self) -> Dict[str, int]:
        """Get current buffer levels for monitoring."""
        status = {}
        for buffer_name, buffer_list in self.station_buffers.items():
            status[buffer_name] = len(buffer_list)
        return status
    

    
    async def _metrics_collector(self):
        """Collect and update production metrics."""
        while self.is_running:
            try:
                await self._update_metrics()
                await asyncio.sleep(60 / self.simulation_speed)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(10)
    
    async def _update_metrics(self):
        """Update production line metrics."""
        if not self.start_time:
            return
        
        runtime = datetime.now() - self.start_time
        runtime_hours = runtime.total_seconds() / 3600
        
        if runtime_hours > 0:
            self.metrics.throughput_per_hour = self.metrics.total_parts_produced / runtime_hours
        
        if self.metrics.total_parts_produced > 0:
            self.metrics.quality_rate = 1.0 - (self.metrics.total_parts_rejected / self.metrics.total_parts_produced)
        
        # Calculate average cycle time
        if self.completed_parts:
            total_cycle_time = sum(
                (part.processing_history[-1]["end_time"] - part.created_at).total_seconds()
                for part in self.completed_parts
                if part.processing_history
            )
            self.metrics.cycle_time_avg = total_cycle_time / len(self.completed_parts)
    
    def get_production_status(self) -> Dict[str, Any]:
        """Get current production status."""
        machine_statuses = {machine_id: machine.get_status() for machine_id, machine in self.machines.items()}
        
        return {
            "production_line": self.name,
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "machines": machine_statuses,
            "active_orders": len(self.current_orders),
            "active_parts": len(self.active_parts),
            "completed_parts": len(self.completed_parts),
            "metrics": {
                "total_parts_produced": self.metrics.total_parts_produced,
                "total_parts_rejected": self.metrics.total_parts_rejected,
                "quality_rate": self.metrics.quality_rate,
                "throughput_per_hour": self.metrics.throughput_per_hour,
                "cycle_time_avg": self.metrics.cycle_time_avg
            }
        }
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """Get sensor data from all machines."""
        sensor_data = {}
        
        for machine_id, machine in self.machines.items():
            machine_sensors = machine.read_sensors()
            sensor_data[machine_id] = {
                sensor_type: {
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality": reading.quality,
                    "timestamp": reading.timestamp.isoformat()
                }
                for sensor_type, reading in machine_sensors.items()
            }
        
        return sensor_data
    
    def get_actuator_data(self) -> Dict[str, Any]:
        """Get actuator data from all machines."""
        actuator_data = {}
        
        for machine_id, machine in self.machines.items():
            machine_actuators = machine.actuator_data
            actuator_data[machine_id] = {
                actuator_type: {
                    "status": status.status,
                    "power_consumption": status.power_consumption,
                    "timestamp": status.timestamp.isoformat()
                }
                for actuator_type, status in machine_actuators.items()
            }
        
        return actuator_data
    
    def get_machine_status_data(self) -> Dict[str, Any]:
        """Get comprehensive machine status data organized by subtopics."""
        machine_status_data = {}
        
        for machine_id, machine in self.machines.items():
            # Get input and output buffer counts for this machine
            input_buffer = self.station_buffers.get(f"{machine_id}_input", [])
            output_buffer = self.station_buffers.get(f"{machine_id}_output", [])
            
            # Calculate machine metrics
            uptime_hours = machine.total_runtime.total_seconds() / 3600
            
            # Machine production data
            machine_production_data = {
                # Core machine state
                "machine_state": machine.state.value,  # Use .value to get just the string
                "operation_phase": machine.operation_phase.value,  # Use .value to get just the string
                "machine_type": machine.type,
                "machine_name": machine.name,
                
                # Current part information
                "current_part_id": machine.current_part.part_id if machine.current_part else None,
                "current_part_type": machine.current_part.part_type if machine.current_part else None,
                "current_part_station": machine.current_part.current_station if machine.current_part else None,
                "current_part_quality": machine.current_part.quality_status if machine.current_part else None,
                
                # Phase timing
                "phase_start_time": machine.phase_start_time.isoformat(),
                "cycle_time_target": machine.cycle_time,
                "phase_duration_remaining": self._calculate_phase_remaining(machine),
                
                # Buffer status
                "input_buffer_count": len(input_buffer),
                "output_buffer_count": len(output_buffer),
                "input_buffer_parts": [part.part_id for part in input_buffer],
                "output_buffer_parts": [part.part_id for part in output_buffer],
                
                # Production metrics
                "parts_processed_today": machine.parts_processed,
                "total_runtime_hours": round(uptime_hours, 2),
                "last_maintenance": machine.last_maintenance.isoformat(),
                "next_maintenance_due": self._calculate_next_maintenance(machine),
                
                # Add inspection status for inspection machines
                "inspection_status": machine.sensor_data["inspection_result"].value if machine.type == "inspection" and "inspection_result" in machine.sensor_data else None,
                
                # Timestamp
                "timestamp": datetime.now().isoformat()
            }
            
            # Add malfunction information if applicable
            if machine.state.value == "malfunction" and hasattr(machine, 'malfunction_start_time') and machine.malfunction_start_time:
                elapsed_malfunction = (datetime.now() - machine.malfunction_start_time).total_seconds()
                remaining_malfunction = max(0, machine.malfunction_duration - elapsed_malfunction)
                machine_production_data.update({
                    "malfunction_duration_remaining": round(remaining_malfunction, 1),
                    "malfunction_elapsed": round(elapsed_malfunction, 1)
                })
            
            # Sensor and actuator data
            sensor_actuator_data = {
                "sensors": {},
                "actuators": {}
            }
            
            # Get sensor readings
            machine_sensors = machine.read_sensors()
            for sensor_type, reading in machine_sensors.items():
                sensor_actuator_data["sensors"][sensor_type] = {
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality": reading.quality,
                    "timestamp": reading.timestamp.isoformat()
                }
            
            # Get actuator data
            for actuator_type, status in machine.actuator_data.items():
                sensor_actuator_data["actuators"][actuator_type] = {
                    "status": status.status,
                    "power_consumption": status.power_consumption,
                    "timestamp": status.timestamp.isoformat()
                }
            
            machine_status_data[machine_id] = {
                "machine_production_data": machine_production_data,
                "sensor_actuator_data": sensor_actuator_data
            }
        
        return machine_status_data
    
    def _calculate_phase_remaining(self, machine) -> float:
        """Calculate remaining time in current operation phase."""
        if not hasattr(machine, 'phase_durations') or machine.operation_phase == "idle":
            return 0.0
        
        phase_duration = machine.phase_durations.get(machine.operation_phase, 0)
        elapsed = (datetime.now() - machine.phase_start_time).total_seconds()
        remaining = max(0, phase_duration - elapsed)
        
        return round(remaining, 1)
    
    def _calculate_next_maintenance(self, machine) -> str:
        """Calculate when next maintenance is due."""
        # Maintenance every 168 hours (1 week) or 1000 parts
        hours_since_maintenance = (datetime.now() - machine.last_maintenance).total_seconds() / 3600
        parts_since_maintenance = machine.parts_processed % 1000
        
        # Next maintenance based on time (168 hours)
        next_time_maintenance = machine.last_maintenance + timedelta(hours=168)
        
        # Or based on parts (every 1000 parts)
        parts_until_maintenance = 1000 - parts_since_maintenance
        
        if hours_since_maintenance >= 160:  # Warning 8 hours before
            return f"DUE_SOON ({168 - hours_since_maintenance:.1f}h)"
        elif parts_until_maintenance <= 50:  # Warning 50 parts before
            return f"DUE_SOON ({parts_until_maintenance} parts)"
        else:
            return next_time_maintenance.strftime("%Y-%m-%d %H:%M")
