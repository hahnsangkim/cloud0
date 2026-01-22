"""
Circuit component models for safety simulator
IEC 62368-1 compliant electrical circuit safety analysis
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


class ComponentType(Enum):
    """Types of circuit components"""
    # Passive components
    RESISTOR = "resistor"
    DIODE = "diode"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"

    # Active components
    IC = "ic"
    FET = "fet"
    LDO = "ldo"
    DCDC = "dcdc"
    PMU = "pmu"

    # Power sources
    ADAPTER = "adapter"
    BATTERY = "battery"

    # Sinks
    SINK = "sink"


class ProtectionType(Enum):
    """Types of protection mechanisms (safeguards)"""
    OVP = "over_voltage_protection"
    OCP = "over_current_protection"
    OTP = "over_temperature_protection"
    UVP = "under_voltage_protection"
    UTP = "under_temperature_protection"
    CURRENT_LIMIT = "current_limit"
    FUSE = "fuse"


class SafetyLevel(Enum):
    """IEC 62368-1 safety power levels"""
    P1 = "P1"  # <= 15W
    P2 = "P2"  # > 15W and <= 100W
    P3 = "P3"  # > 100W


@dataclass
class Protection:
    """Safeguard protection mechanism"""
    type: ProtectionType
    threshold_voltage: Optional[float] = None  # Volts
    threshold_current: Optional[float] = None  # Amperes
    threshold_temperature: Optional[float] = None  # Celsius
    threshold_power: Optional[float] = None  # Watts
    response_time: Optional[float] = None  # Seconds

    def __str__(self):
        return f"{self.type.value}"


@dataclass
class Component:
    """Base component class"""
    id: str
    component_type: ComponentType
    name: str
    voltage_nominal: Optional[float] = None  # Volts
    voltage_min: Optional[float] = None
    voltage_max: Optional[float] = None
    current_nominal: Optional[float] = None  # Amperes
    current_min: Optional[float] = None
    current_max: Optional[float] = None
    power_rating: Optional[float] = None  # Watts

    def __str__(self):
        return f"{self.name} ({self.id})"

    def is_passive(self) -> bool:
        """Check if component is passive"""
        return self.component_type in [
            ComponentType.RESISTOR,
            ComponentType.DIODE,
            ComponentType.CAPACITOR,
            ComponentType.INDUCTOR
        ]

    def is_active(self) -> bool:
        """Check if component is active"""
        return self.component_type in [
            ComponentType.IC,
            ComponentType.FET,
            ComponentType.LDO,
            ComponentType.DCDC,
            ComponentType.PMU
        ]

    def is_source(self) -> bool:
        """Check if component is a power source"""
        return self.component_type in [
            ComponentType.ADAPTER,
            ComponentType.BATTERY
        ]

    def is_sink(self) -> bool:
        """Check if component is a power sink"""
        return self.component_type == ComponentType.SINK


@dataclass
class PassiveComponent(Component):
    """Passive component (resistor, capacitor, inductor, diode)"""
    resistance: Optional[float] = None  # Ohms
    capacitance: Optional[float] = None  # Farads
    inductance: Optional[float] = None  # Henrys
    forward_voltage: Optional[float] = None  # Volts (for diodes)

    def __post_init__(self):
        if not self.is_passive():
            raise ValueError(f"Component type {self.component_type} is not passive")


@dataclass
class ActiveComponent(Component):
    """Active component (IC, FET, LDO, DCDC, PMU)"""
    certified: bool = False  # Certified components have non-safety-violent failures
    protections: List[Protection] = field(default_factory=list)
    efficiency: Optional[float] = None  # 0.0 to 1.0

    # Components attached to this active component
    attached_passives: List[str] = field(default_factory=list)  # List of component IDs

    def __post_init__(self):
        if not self.is_active():
            raise ValueError(f"Component type {self.component_type} is not active")

    def has_protection(self, protection_type: ProtectionType) -> bool:
        """Check if component has specific protection"""
        return any(p.type == protection_type for p in self.protections)

    def get_protection(self, protection_type: ProtectionType) -> Optional[Protection]:
        """Get protection mechanism by type"""
        for p in self.protections:
            if p.type == protection_type:
                return p
        return None


@dataclass
class PowerSource(Component):
    """Power source (adapter, battery)"""
    voltage_output: float = 0.0  # Volts
    current_max: float = 0.0  # Amperes
    power_max: float = 0.0  # Watts

    def __post_init__(self):
        if not self.is_source():
            raise ValueError(f"Component type {self.component_type} is not a source")

        # Calculate power if not specified
        if self.power_max == 0.0 and self.voltage_output and self.current_max:
            self.power_max = self.voltage_output * self.current_max


@dataclass
class PowerSink(Component):
    """Power sink (function endpoint)"""
    power_consumption: float = 0.0  # Watts
    voltage_required: float = 0.0  # Volts
    current_required: float = 0.0  # Amperes

    def __post_init__(self):
        if not self.is_sink():
            raise ValueError(f"Component type {self.component_type} is not a sink")


@dataclass
class Connection:
    """Connection between components"""
    from_component: str  # Component ID
    to_component: str  # Component ID
    connection_type: str = "power"  # power, ground, signal
    resistance: float = 0.0  # Trace resistance in Ohms

    def __str__(self):
        return f"{self.from_component} -> {self.to_component}"


@dataclass
class CircuitState:
    """State of the circuit at a point in time"""
    voltage_map: Dict[str, float] = field(default_factory=dict)  # component_id -> voltage
    current_map: Dict[str, float] = field(default_factory=dict)  # component_id -> current
    power_map: Dict[str, float] = field(default_factory=dict)  # component_id -> power
    temperature_map: Dict[str, float] = field(default_factory=dict)  # component_id -> temperature

    def get_power(self, component_id: str) -> float:
        """Get power at component"""
        return self.power_map.get(component_id, 0.0)

    def get_voltage(self, component_id: str) -> float:
        """Get voltage at component"""
        return self.voltage_map.get(component_id, 0.0)

    def get_current(self, component_id: str) -> float:
        """Get current at component"""
        return self.current_map.get(component_id, 0.0)

    def classify_safety_level(self, power: float) -> SafetyLevel:
        """Classify power level according to IEC 62368-1"""
        if power <= 15.0:
            return SafetyLevel.P1
        elif power <= 100.0:
            return SafetyLevel.P2
        else:
            return SafetyLevel.P3

    def is_safety_violation(self, power: float) -> bool:
        """Check if power level violates safety (P2 or P3)"""
        return power > 15.0
