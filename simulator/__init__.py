"""
Electrical Circuit Safety Simulator
IEC 62368-1 Compliance Analysis
"""

from .components import (
    Component,
    ActiveComponent,
    PassiveComponent,
    PowerSource,
    PowerSink,
    ComponentType,
    Protection,
    ProtectionType,
    SafetyLevel,
    Connection,
    CircuitState
)

from .circuit import Circuit
from .power_analysis import PowerFlowAnalyzer
from .fault_simulator import FaultSimulator, FaultCondition, FaultScenario, SafetyViolation
from .parser import CircuitParser
from .reporter import SafetyReporter

__version__ = "1.0.0"

__all__ = [
    # Components
    'Component',
    'ActiveComponent',
    'PassiveComponent',
    'PowerSource',
    'PowerSink',
    'ComponentType',
    'Protection',
    'ProtectionType',
    'SafetyLevel',
    'Connection',
    'CircuitState',

    # Circuit
    'Circuit',

    # Analysis
    'PowerFlowAnalyzer',
    'FaultSimulator',
    'FaultCondition',
    'FaultScenario',
    'SafetyViolation',

    # Utilities
    'CircuitParser',
    'SafetyReporter'
]
