"""Machine model for production line simulation."""

import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MachineState(Enum):
    """Machine operational states."""
    STOPPED = "stopped"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    IDLE = "idle"
    MALFUNCTION = "malfunction"


class SensorType(Enum):
    """Types of sensors available."""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    FORCE = "force"
    POSITION = "position"
    PART_PRESENT = "part_present"
    TORQUE = "torque"
    WEIGHT = "weight"
    CAMERA = "camera"
    LASER_MEASUREMENT = "laser_measurement"


class ActuatorType(Enum):
    """Types of actuators available."""
    CONVEYOR = "conveyor"
    PNEUMATIC_CLAMP = "pneumatic_clamp"
    HEATING_ELEMENT = "heating_element"
    ROBOT_ARM = "robot_arm"
    SCREWDRIVER = "screwdriver"
    PICK_AND_PLACE = "pick_and_place"
    REJECT_PUSHER = "reject_pusher"
    SORTING_GATE = "sorting_gate"


class OperationPhase(Enum):
    """Machine operation phases for realistic simulation."""
    IDLE = "idle"
    LOADING = "loading"
    PROCESSING = "processing"
    UNLOADING = "unloading"
    # Station 1 specific phases
    HEATING = "heating"
    COOLING = "cooling"
    CLAMPING = "clamping"
    RELEASING = "releasing"
    # Station 2 specific phases
    POSITIONING = "positioning"
    ASSEMBLING = "assembling"
    FASTENING = "fastening"
    # Station 3 specific phases
    INSPECTING = "inspecting"
    MEASURING = "measuring"
    SORTING = "sorting"


class ActuatorState(Enum):
    """Actuator operational states."""
    STOPPED = "stopped"
    IDLE = "idle"
    RUNNING = "running"
    MOVING = "moving"
    WORKING = "working"
    ERROR = "error"
    # Conveyor specific
    RUNNING_SLOW = "running_slow"
    RUNNING_FAST = "running_fast"
    # Clamp specific
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    OPENING = "opening"
    # Heating specific
    OFF = "off"
    HEATING = "heating"
    MAINTAINING = "maintaining"
    COOLING = "cooling"
    # Robot arm specific
    MOVING_TO_PICKUP = "moving_to_pickup"
    PICKING = "picking"
    MOVING_TO_ASSEMBLY = "moving_to_assembly"
    ASSEMBLING = "assembling"
    RETURNING = "returning"
    # Screwdriver specific
    ENGAGING = "engaging"
    DRIVING = "driving"
    BACKING_OUT = "backing_out"
    DISENGAGED = "disengaged"
    # Pusher specific
    RETRACTED = "retracted"
    EXTENDING = "extending"
    EXTENDED = "extended"
    RETRACTING = "retracting"


@dataclass
class SensorReading:
    """Represents a sensor reading."""
    sensor_type: str
    value: Any
    timestamp: datetime
    unit: str
    quality: str = "good"  # good, poor, bad


@dataclass
class ActuatorStatus:
    """Represents actuator status."""
    actuator_type: str
    status: str  # Now uses ActuatorState enum values
    timestamp: datetime
    power_consumption: float = 0.0  # watts
    target_value: Optional[float] = None  # For position/speed targets
    actual_value: Optional[float] = None  # Current position/speed


@dataclass
class ProductionPart:
    """Represents a part in production."""
    part_id: str
    part_type: str
    created_at: datetime
    current_station: Optional[str] = None
    quality_status: str = "unknown"  # pass, fail, unknown
    processing_history: List[Dict[str, Any]] = field(default_factory=list)


class Machine:
    """Simulates a production line machine with sensors and actuators."""
    
    def __init__(self, config: Dict[str, Any], simulation_speed: float = 1.0):
        self.config = config
        self.id = config["id"]
        self.name = config["name"]
        self.type = config["type"]
        self.cycle_time = config.get("cycle_time", 30)
        self.failure_rate = config.get("failure_rate", 0.02)  # Used for malfunction simulation
        self.simulation_speed = simulation_speed
        
        # Machine state
        self.state = MachineState.STOPPED
        self.operation_phase = OperationPhase.IDLE
        self.phase_start_time = datetime.now()
        self.current_part: Optional[ProductionPart] = None
        self.parts_processed = 0
        self.total_runtime = timedelta()
        self.last_maintenance = datetime.now()
        
        # Malfunction simulation
        self.malfunction_start_time: Optional[datetime] = None
        self.malfunction_duration: float = 0.0
        
        # Sensors and actuators
        self.sensors = config.get("sensors", [])
        self.actuators = config.get("actuators", [])
        
        # Simulation data
        self.sensor_data: Dict[str, SensorReading] = {}
        self.actuator_data: Dict[str, ActuatorStatus] = {}
        
        # Phase timing and targets
        self.phase_durations = self._get_phase_durations()
        self.sensor_targets = {}
        
        self.logger = logging.getLogger(f"{__name__}.{self.id}")
        
        # Initialize sensor baselines
        self._initialize_sensor_baselines()
    
    def _get_phase_durations(self) -> Dict[str, float]:
        """Get phase durations based on machine type."""
        if self.type == "preparation":
            return {
                "loading": 3.0,
                "heating": 8.0,
                "clamping": 2.0,
                "processing": 10.0,
                "cooling": 5.0,
                "releasing": 2.0,
                "unloading": 3.0
            }
        elif self.type == "assembly":
            return {
                "loading": 4.0,
                "positioning": 6.0,
                "assembling": 15.0,
                "fastening": 8.0,
                "unloading": 4.0
            }
        elif self.type == "inspection":
            return {
                "loading": 2.0,
                "inspecting": 8.0,
                "measuring": 6.0,
                "sorting": 3.0,
                "unloading": 2.0
            }
        else:
            return {"processing": self.cycle_time}
    
    def _initialize_sensor_baselines(self):
        """Initialize baseline values for sensors."""
        self.sensor_baselines = {
            "temperature": 25.0,  # °C
            "pressure": 2.0,      # bar
            "vibration": 1.0,     # mm/s
            "force": 100.0,       # N
            "position": 0.0,      # mm
            "part_present": False, # bool
            "torque": 10.0,       # Nm
            "weight": 1.5,        # kg
            "camera": 1920*1080,  # pixels (image resolution)
            "laser_measurement": 50.0  # mm
        }
    
    async def start(self):
        """Start the machine."""
        self.logger.info(f"Starting machine {self.name}")
        self.state = MachineState.IDLE
        self.operation_phase = OperationPhase.IDLE
        
        # Initialize all actuators to their idle states
        for actuator in self.actuators:
            initial_state = self._get_initial_actuator_state(actuator)
            power = self._get_actuator_power(actuator, initial_state)
            
            self.actuator_data[actuator] = ActuatorStatus(
                actuator_type=actuator,
                status=initial_state,
                timestamp=datetime.now(),
                power_consumption=power
            )
    
    def _get_initial_actuator_state(self, actuator: str) -> str:
        """Get the initial state for each actuator type."""
        if actuator == "conveyor":
            return ActuatorState.STOPPED.value
        elif actuator == "pneumatic_clamp":
            return ActuatorState.OPEN.value
        elif actuator == "heating_element":
            return ActuatorState.OFF.value
        elif actuator == "robot_arm":
            return ActuatorState.IDLE.value
        elif actuator == "screwdriver":
            return ActuatorState.DISENGAGED.value
        elif actuator == "pick_and_place":
            return ActuatorState.IDLE.value
        elif actuator == "reject_pusher":
            return ActuatorState.RETRACTED.value
        elif actuator == "sorting_gate":
            return ActuatorState.IDLE.value
        else:
            return ActuatorState.IDLE.value
    
    def _get_actuator_power(self, actuator: str, state: str) -> float:
        """Get power consumption for actuator in given state."""
        base_power = {
            "conveyor": {"idle": 50, "running": 150, "running_fast": 200},
            "pneumatic_clamp": {"open": 30, "closing": 100, "closed": 80, "opening": 100},
            "heating_element": {"off": 0, "heating": 500, "maintaining": 300, "cooling": 50},
            "robot_arm": {"idle": 75, "moving": 250, "working": 300},
            "screwdriver": {"disengaged": 25, "engaging": 120, "driving": 200},
            "pick_and_place": {"idle": 60, "moving": 180, "working": 220},
            "reject_pusher": {"retracted": 20, "extending": 80, "extended": 40},
            "sorting_gate": {"idle": 30, "moving": 90, "working": 60}
        }
        
        actuator_powers = base_power.get(actuator, {"idle": 50, "working": 150})
        return actuator_powers.get(state.split("_")[0], actuator_powers.get("idle", 50)) + random.uniform(-10, 10)
    
    async def stop(self):
        """Stop the machine."""
        self.logger.info(f"Stopping machine {self.name}")
        self.state = MachineState.STOPPED
        
        # Stop all actuators
        for actuator in self.actuators:
            if actuator in self.actuator_data:
                self.actuator_data[actuator].status = "stopped"
                self.actuator_data[actuator].timestamp = datetime.now()
                self.actuator_data[actuator].power_consumption = 0.0
    
    async def process_part(self, part: ProductionPart) -> ProductionPart:
        """Process a part through this machine with realistic phase-based operation."""
        if self.state != MachineState.IDLE:
            raise ValueError(f"Machine {self.id} is not ready to process parts")
        
        self.logger.info(f"Processing part {part.part_id} on machine {self.name}")
        self.current_part = part
        self.state = MachineState.RUNNING
        part.current_station = self.id
        
        start_time = datetime.now()
        
        try:
            # Execute machine-specific processing phases
            if self.type == "preparation":
                await self._process_preparation_phases(part)
            elif self.type == "assembly":
                await self._process_assembly_phases(part)
            elif self.type == "inspection":
                await self._process_inspection_phases(part)
            else:
                # Generic processing for unknown types
                await self._process_generic_phases(part)
            
            # Check for random malfunction
            if random.random() < self.failure_rate:
                await self._simulate_malfunction()
                # Don't fail the part, just causes delay
            
            # Set default quality if not already set by specific processing
            if part.quality_status == "unknown":
                part.quality_status = "pass"
            
        except Exception as e:
            self.logger.error(f"Error processing part {part.part_id}: {e}")
            part.quality_status = "error"
        
        # Record processing history
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        processing_record = {
            "machine_id": self.id,
            "machine_name": self.name,
            "start_time": start_time,
            "end_time": end_time,
            "processing_time": processing_time,
            "quality_status": part.quality_status
        }
        part.processing_history.append(processing_record)
        
        # Update metrics
        self.parts_processed += 1
        self.total_runtime += timedelta(seconds=processing_time)
        
        # Return to idle state
        await self._transition_to_idle()
        
        self.logger.info(f"Finished processing part {part.part_id} - Status: {part.quality_status}")
        return part
    
    async def _process_preparation_phases(self, part: ProductionPart):
        """Process through preparation station phases."""
        # Phase 1: Loading
        await self._execute_phase(OperationPhase.LOADING, {
            "conveyor": ActuatorState.RUNNING_SLOW.value,
            "pneumatic_clamp": ActuatorState.OPEN.value
        })
        
        # Phase 2: Clamping
        await self._execute_phase(OperationPhase.CLAMPING, {
            "conveyor": ActuatorState.STOPPED.value,
            "pneumatic_clamp": ActuatorState.CLOSING.value
        })
        
        # Phase 3: Heating
        await self._execute_phase(OperationPhase.HEATING, {
            "pneumatic_clamp": ActuatorState.CLOSED.value,
            "heating_element": ActuatorState.HEATING.value
        })
        
        # Phase 4: Processing (maintaining temperature)
        await self._execute_phase(OperationPhase.PROCESSING, {
            "heating_element": ActuatorState.MAINTAINING.value
        })
        
        # Phase 5: Cooling
        await self._execute_phase(OperationPhase.COOLING, {
            "heating_element": ActuatorState.COOLING.value
        })
        
        # Phase 6: Releasing
        await self._execute_phase(OperationPhase.RELEASING, {
            "heating_element": ActuatorState.OFF.value,
            "pneumatic_clamp": ActuatorState.OPENING.value
        })
        
        # Phase 7: Unloading
        await self._execute_phase(OperationPhase.UNLOADING, {
            "pneumatic_clamp": ActuatorState.OPEN.value,
            "conveyor": ActuatorState.RUNNING.value
        })
    
    async def _process_assembly_phases(self, part: ProductionPart):
        """Process through assembly station phases."""
        # Phase 1: Loading
        await self._execute_phase(OperationPhase.LOADING, {
            "conveyor": ActuatorState.RUNNING_SLOW.value,
            "robot_arm": ActuatorState.IDLE.value
        })
        
        # Phase 2: Positioning
        await self._execute_phase(OperationPhase.POSITIONING, {
            "conveyor": ActuatorState.STOPPED.value,
            "robot_arm": ActuatorState.MOVING_TO_PICKUP.value,
            "pick_and_place": ActuatorState.MOVING.value
        })
        
        # Phase 3: Assembling
        await self._execute_phase(OperationPhase.ASSEMBLING, {
            "robot_arm": ActuatorState.ASSEMBLING.value,
            "pick_and_place": ActuatorState.WORKING.value
        })
        
        # Phase 4: Fastening
        await self._execute_phase(OperationPhase.FASTENING, {
            "screwdriver": ActuatorState.ENGAGING.value
        }, lambda: asyncio.sleep(2 / self.simulation_speed))
        
        await self._execute_phase(OperationPhase.FASTENING, {
            "screwdriver": ActuatorState.DRIVING.value
        })
        
        # Phase 5: Unloading
        await self._execute_phase(OperationPhase.UNLOADING, {
            "screwdriver": ActuatorState.DISENGAGED.value,
            "robot_arm": ActuatorState.RETURNING.value,
            "conveyor": ActuatorState.RUNNING.value
        })
    
    async def _process_inspection_phases(self, part: ProductionPart):
        """Process through inspection station phases."""
        # Phase 1: Loading
        await self._execute_phase(OperationPhase.LOADING, {
            "conveyor": ActuatorState.RUNNING_SLOW.value,
            "sorting_gate": ActuatorState.IDLE.value
        })
        
        # Phase 2: Inspecting (visual)
        await self._execute_phase(OperationPhase.INSPECTING, {
            "conveyor": ActuatorState.STOPPED.value
        })
        
        # Phase 3: Measuring (dimensional)
        await self._execute_phase(OperationPhase.MEASURING, {})
        
        # Determine inspection result - 95% pass rate
        quality_ok = random.random() > 0.05
        inspection_status = "ok" if quality_ok else "nok"
        
        # Store inspection result in part
        part.quality_status = "pass" if quality_ok else "reject"
        
        # Add inspection data to sensor readings for monitoring
        inspection_reading = SensorReading(
            sensor_type="inspection_result",
            value=inspection_status,
            timestamp=datetime.now(),
            unit="status",
            quality="good"
        )
        self.sensor_data["inspection_result"] = inspection_reading
        
        # Phase 4: Sorting (based on inspection result)
        if quality_ok:
            await self._execute_phase(OperationPhase.SORTING, {
                "conveyor": ActuatorState.RUNNING.value,
                "sorting_gate": ActuatorState.IDLE.value
            })
        else:
            await self._execute_phase(OperationPhase.SORTING, {
                "reject_pusher": ActuatorState.EXTENDING.value,
                "sorting_gate": ActuatorState.WORKING.value
            })
            # Reset reject pusher
            await asyncio.sleep(1 / self.simulation_speed)
            self._update_actuator_state("reject_pusher", ActuatorState.RETRACTING.value)
        
        # Phase 5: Unloading
        await self._execute_phase(OperationPhase.UNLOADING, {
            "conveyor": ActuatorState.RUNNING.value,
            "reject_pusher": ActuatorState.RETRACTED.value,
            "sorting_gate": ActuatorState.IDLE.value
        })
    
    async def _process_generic_phases(self, part: ProductionPart):
        """Generic processing for unknown machine types."""
        await self._execute_phase(OperationPhase.PROCESSING, {})
    
    async def _execute_phase(self, phase: OperationPhase, actuator_states: Dict[str, str], custom_action=None):
        """Execute a specific operation phase."""
        self.operation_phase = phase
        self.phase_start_time = datetime.now()
        
        # Update actuator states
        for actuator, state in actuator_states.items():
            if actuator in self.actuator_data:
                self._update_actuator_state(actuator, state)
        
        # Execute custom action if provided
        if custom_action:
            await custom_action()
        
        # Wait for phase duration
        duration = self.phase_durations.get(phase.value, 5.0)
        await asyncio.sleep(duration / self.simulation_speed)
    
    def _update_actuator_state(self, actuator: str, state: str):
        """Update actuator state and power consumption."""
        if actuator in self.actuator_data:
            self.actuator_data[actuator].status = state
            self.actuator_data[actuator].timestamp = datetime.now()
            self.actuator_data[actuator].power_consumption = self._get_actuator_power(actuator, state)
    
    async def _transition_to_idle(self):
        """Transition machine and all actuators to idle state."""
        self.state = MachineState.IDLE
        self.operation_phase = OperationPhase.IDLE
        self.current_part = None
        
        # Reset all actuators to idle states
        for actuator in self.actuators:
            idle_state = self._get_initial_actuator_state(actuator)
            self._update_actuator_state(actuator, idle_state)
    
    async def _simulate_malfunction(self):
        """Simulate a malfunction based on failure rate."""
        if random.random() < self.failure_rate:
            self.logger.warning(f"Machine {self.name} experienced a malfunction")
            self.state = MachineState.MALFUNCTION
            
            # Record malfunction start time and generate random duration
            self.malfunction_start_time = datetime.now()
            self.malfunction_duration = random.uniform(30, 180) / self.simulation_speed  # 30 seconds to 3 minutes
            
            # Wait for malfunction to resolve
            await asyncio.sleep(self.malfunction_duration)
            
            self.logger.info(f"Machine {self.name} recovered from malfunction after {self.malfunction_duration:.1f} seconds")
            self.state = MachineState.IDLE
            self.malfunction_start_time = None
            self.malfunction_duration = 0.0
            return True
        return False
    
    async def _check_malfunction_recovery(self):
        """Check if machine should recover from malfunction."""
        if self.state == MachineState.MALFUNCTION and self.malfunction_start_time:
            elapsed = (datetime.now() - self.malfunction_start_time).total_seconds()
            if elapsed >= self.malfunction_duration:
                self.logger.info(f"Machine {self.name} recovered from malfunction after {elapsed:.1f} seconds")
                self.state = MachineState.IDLE
                self.malfunction_start_time = None
                self.malfunction_duration = 0.0
                return True
        return False
    
    def read_sensors(self) -> Dict[str, SensorReading]:
        """Read all sensor values."""
        current_time = datetime.now()
        
        for sensor in self.sensors:
            value = self._generate_sensor_value(sensor)
            quality = self._determine_sensor_quality(sensor, value)
            
            self.sensor_data[sensor] = SensorReading(
                sensor_type=sensor,
                value=value,
                timestamp=current_time,
                unit=self._get_sensor_unit(sensor),
                quality=quality
            )
        
        return self.sensor_data
    
    def _generate_sensor_value(self, sensor_type: str) -> Any:
        """Generate realistic phase-aware sensor values based on machine state and operation phase."""
        baseline = self.sensor_baselines.get(sensor_type, 0)
        
        if sensor_type == "part_present":
            return self.current_part is not None
        
        # Phase-specific sensor value generation
        if self.type == "preparation":
            return self._generate_preparation_sensor_value(sensor_type, baseline)
        elif self.type == "assembly":
            return self._generate_assembly_sensor_value(sensor_type, baseline)
        elif self.type == "inspection":
            return self._generate_inspection_sensor_value(sensor_type, baseline)
        else:
            return self._generate_generic_sensor_value(sensor_type, baseline)
    
    def _generate_preparation_sensor_value(self, sensor_type: str, baseline: float) -> Any:
        """Generate sensor values for preparation station based on operation phase."""
        if sensor_type == "temperature":
            if self.operation_phase == OperationPhase.IDLE:
                return round(25.0 + random.uniform(-2, 2), 1)
            elif self.operation_phase == OperationPhase.HEATING:
                # Temperature rising from 25°C to 85°C
                phase_progress = self._get_phase_progress()
                target_temp = 25 + (85 - 25) * phase_progress
                return round(target_temp + random.uniform(-3, 3), 1)
            elif self.operation_phase == OperationPhase.PROCESSING:
                # Maintaining temperature around 80°C
                return round(80.0 + random.uniform(-5, 5), 1)
            elif self.operation_phase == OperationPhase.COOLING:
                # Temperature cooling from 85°C to 30°C
                phase_progress = self._get_phase_progress()
                target_temp = 85 - (85 - 30) * phase_progress
                return round(target_temp + random.uniform(-3, 3), 1)
            else:
                return round(baseline + random.uniform(-5, 10), 1)
                
        elif sensor_type == "pressure":
            if self.operation_phase in [OperationPhase.CLAMPING, OperationPhase.PROCESSING]:
                # High pressure during clamping/processing
                return round(1.8 + random.uniform(-0.2, 0.3), 2)
            elif self.operation_phase == OperationPhase.RELEASING:
                # Pressure dropping during release
                phase_progress = self._get_phase_progress()
                target_pressure = 1.8 - (1.8 - 0.5) * phase_progress
                return round(target_pressure + random.uniform(-0.1, 0.1), 2)
            else:
                # Standby pressure
                return round(0.5 + random.uniform(-0.1, 0.1), 2)
                
        elif sensor_type == "vibration":
            if self.operation_phase in [OperationPhase.PROCESSING, OperationPhase.HEATING]:
                return round(1.0 + random.uniform(0.2, 0.8), 2)
            else:
                return round(0.5 + random.uniform(-0.2, 0.2), 2)
                
        return self._generate_generic_sensor_value(sensor_type, baseline)
    
    def _generate_assembly_sensor_value(self, sensor_type: str, baseline: float) -> Any:
        """Generate sensor values for assembly station based on operation phase."""
        if sensor_type == "force":
            if self.operation_phase == OperationPhase.IDLE:
                return round(random.uniform(0, 10), 0)
            elif self.operation_phase == OperationPhase.POSITIONING:
                return round(random.uniform(20, 40), 0)
            elif self.operation_phase == OperationPhase.ASSEMBLING:
                return round(random.uniform(80, 120), 0)
            elif self.operation_phase == OperationPhase.FASTENING:
                return round(random.uniform(100, 150), 0)
            else:
                return round(random.uniform(5, 15), 0)
                
        elif sensor_type == "position":
            if self.operation_phase == OperationPhase.IDLE:
                return round(0.0 + random.uniform(-1, 1), 1)
            elif self.operation_phase == OperationPhase.POSITIONING:
                # Moving to pickup position
                phase_progress = self._get_phase_progress()
                target_pos = 150.0 * phase_progress
                return round(target_pos + random.uniform(-2, 2), 1)
            elif self.operation_phase == OperationPhase.ASSEMBLING:
                return round(75.0 + random.uniform(-3, 3), 1)
            elif self.operation_phase == OperationPhase.FASTENING:
                return round(50.0 + random.uniform(-2, 2), 1)
            else:
                return round(baseline + random.uniform(-5, 5), 1)
                
        elif sensor_type == "torque":
            if self.operation_phase == OperationPhase.FASTENING:
                return round(10.0 + random.uniform(5, 15), 1)
            elif self.operation_phase in [OperationPhase.ASSEMBLING, OperationPhase.POSITIONING]:
                return round(2.0 + random.uniform(0, 3), 1)
            else:
                return round(0.5 + random.uniform(-0.5, 1), 1)
                
        return self._generate_generic_sensor_value(sensor_type, baseline)
    
    def _generate_inspection_sensor_value(self, sensor_type: str, baseline: float) -> Any:
        """Generate sensor values for inspection station based on operation phase."""
        if sensor_type == "weight":
            if self.current_part:
                # Weight varies slightly during inspection
                base_weight = 1.5
                if self.operation_phase == OperationPhase.MEASURING:
                    return round(base_weight + random.uniform(-0.05, 0.05), 3)
                else:
                    return round(base_weight + random.uniform(-0.1, 0.1), 3)
            else:
                return 0.0
                
        elif sensor_type == "camera":
            if self.operation_phase == OperationPhase.INSPECTING:
                # Full resolution during inspection
                return 1920 * 1080
            elif self.current_part:
                # Lower resolution or processing values
                return random.randint(500000, 1500000)
            else:
                return 0
                
        elif sensor_type == "laser_measurement":
            if self.operation_phase == OperationPhase.MEASURING:
                # Precise measurement with small variation
                return round(50.0 + random.uniform(-0.5, 0.5), 2)
            elif self.current_part:
                return round(50.0 + random.uniform(-1, 1), 2)
            else:
                return 0.0
                
        return self._generate_generic_sensor_value(sensor_type, baseline)
    
    def _generate_generic_sensor_value(self, sensor_type: str, baseline: float) -> Any:
        """Generate generic sensor values with basic variation."""
        if self.state == MachineState.RUNNING:
            variation_factor = 1.2
        elif self.state == MachineState.ERROR:
            variation_factor = 2.0
        else:
            variation_factor = 1.0
            
        value = baseline + random.uniform(-0.1, 0.1) * baseline * variation_factor
        return round(value, 2)
    
    def _get_phase_progress(self) -> float:
        """Get progress through current phase (0.0 to 1.0)."""
        if not hasattr(self, 'phase_start_time'):
            return 0.0
            
        elapsed = (datetime.now() - self.phase_start_time).total_seconds()
        duration = self.phase_durations.get(self.operation_phase.value, 5.0)
        return min(1.0, elapsed / duration)
    
    def _determine_sensor_quality(self, sensor_type: str, value: Any) -> str:
        """Determine sensor reading quality."""
        if self.state == MachineState.ERROR:
            return "bad" if random.random() < 0.5 else "poor"
        elif random.random() < 0.95:
            return "good"
        else:
            return "poor"
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """Get the unit for a sensor type."""
        units = {
            "temperature": "°C",
            "pressure": "bar",
            "vibration": "mm/s",
            "force": "N",
            "torque": "Nm",
            "weight": "kg",
            "position": "mm",
            "part_present": "bool",
            "camera": "pixels",
            "laser_measurement": "mm"
        }
        return units.get(sensor_type, "unit")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current machine status organized by data subtopics."""
        # Basic machine production data
        machine_production_data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "state": self.state.value,
            "operation_phase": self.operation_phase.value,
            "current_part": self.current_part.part_id if self.current_part else None,
            "parts_processed": self.parts_processed,
            "total_runtime_hours": round(self.total_runtime.total_seconds() / 3600, 2),
            "last_maintenance": self.last_maintenance.isoformat()
        }
        
        # Add malfunction information if applicable
        if self.state == MachineState.MALFUNCTION and self.malfunction_start_time:
            elapsed_malfunction = (datetime.now() - self.malfunction_start_time).total_seconds()
            remaining_malfunction = max(0, self.malfunction_duration - elapsed_malfunction)
            machine_production_data.update({
                "malfunction_duration_remaining": round(remaining_malfunction, 1),
                "malfunction_elapsed": round(elapsed_malfunction, 1)
            })
        
        # Sensor and actuator data
        sensor_actuator_data = {
            "sensors": {
                sensor_type: {
                    "value": reading.value,
                    "unit": reading.unit,
                    "quality": reading.quality,
                    "timestamp": reading.timestamp.isoformat()
                }
                for sensor_type, reading in self.sensor_data.items()
            },
            "actuators": {
                actuator_type: {
                    "status": status.status,
                    "power_consumption": status.power_consumption,
                    "timestamp": status.timestamp.isoformat()
                }
                for actuator_type, status in self.actuator_data.items()
            }
        }
        
        return {
            "machine_production_data": machine_production_data,
            "sensor_actuator_data": sensor_actuator_data
        }
