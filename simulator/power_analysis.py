"""
Power flow analysis and calculation engine
"""

from typing import Dict, List, Optional
import math

from .components import (
    Component, ActiveComponent, PassiveComponent, PowerSource, PowerSink,
    CircuitState, ComponentType, ProtectionType
)
from .circuit import Circuit


class PowerFlowAnalyzer:
    """Analyze power flow through circuit"""

    def __init__(self, circuit: Circuit):
        self.circuit = circuit

    def calculate_power_flow(
        self,
        failed_components: Optional[List[str]] = None
    ) -> CircuitState:
        """
        Calculate power flow through circuit

        Args:
            failed_components: List of component IDs that have failed

        Returns:
            CircuitState with voltage, current, and power maps
        """
        if failed_components is None:
            failed_components = []

        state = CircuitState()

        # Step 1: Set source voltages
        for source in self.circuit.get_sources():
            if source.id not in failed_components:
                if isinstance(source, PowerSource):
                    state.voltage_map[source.id] = source.voltage_output
                    state.current_map[source.id] = source.current_max
                    state.power_map[source.id] = source.power_max

        # Step 2: Propagate voltage and current through paths
        paths = self.circuit.find_all_paths()

        for path in paths:
            self._analyze_path(path, state, failed_components)

        # Step 3: Calculate power for each component
        for comp_id, component in self.circuit.components.items():
            if comp_id in failed_components:
                continue

            voltage = state.voltage_map.get(comp_id, 0.0)
            current = state.current_map.get(comp_id, 0.0)

            # Calculate power: P = V * I
            power = voltage * current
            state.power_map[comp_id] = power

        return state

    def _analyze_path(
        self,
        path: List[str],
        state: CircuitState,
        failed_components: List[str]
    ) -> None:
        """Analyze a single path from source to sink"""
        if not path:
            return

        # Start with source voltage and current
        current_voltage = state.voltage_map.get(path[0], 0.0)
        current_current = state.current_map.get(path[0], 0.0)

        for i in range(1, len(path)):
            comp_id = path[i]

            if comp_id in failed_components:
                # Failed component - no power flow
                current_voltage = 0.0
                current_current = 0.0
                break

            component = self.circuit.components[comp_id]

            # Check protections on active components
            if isinstance(component, ActiveComponent):
                current_voltage, current_current = self._apply_protections(
                    component, current_voltage, current_current
                )

                # Apply voltage conversion for DC-DC converters, LDOs
                if component.component_type in [ComponentType.DCDC, ComponentType.LDO]:
                    if component.voltage_nominal:
                        current_voltage = component.voltage_nominal

                    # Apply efficiency
                    if component.efficiency:
                        current_current = current_current * component.efficiency

            # Update state
            state.voltage_map[comp_id] = max(
                state.voltage_map.get(comp_id, 0.0),
                current_voltage
            )
            state.current_map[comp_id] = max(
                state.current_map.get(comp_id, 0.0),
                current_current
            )

    def _apply_protections(
        self,
        component: ActiveComponent,
        voltage: float,
        current: float
    ) -> tuple[float, float]:
        """Apply protection mechanisms to voltage and current"""

        # Over-voltage protection
        ovp = component.get_protection(ProtectionType.OVP)
        if ovp and ovp.threshold_voltage:
            if voltage > ovp.threshold_voltage:
                voltage = 0.0  # Protection triggered, cut power
                current = 0.0

        # Under-voltage protection
        uvp = component.get_protection(ProtectionType.UVP)
        if uvp and uvp.threshold_voltage:
            if voltage < uvp.threshold_voltage:
                voltage = 0.0  # Protection triggered, cut power
                current = 0.0

        # Over-current protection
        ocp = component.get_protection(ProtectionType.OCP)
        if ocp and ocp.threshold_current:
            if current > ocp.threshold_current:
                current = 0.0  # Protection triggered, cut power
                voltage = 0.0

        # Current limit (enforced, not protective cutoff)
        current_limit = component.get_protection(ProtectionType.CURRENT_LIMIT)
        if current_limit and current_limit.threshold_current:
            current = min(current, current_limit.threshold_current)

        # Fuse
        fuse = component.get_protection(ProtectionType.FUSE)
        if fuse and fuse.threshold_current:
            if current > fuse.threshold_current:
                current = 0.0  # Fuse blown
                voltage = 0.0

        return voltage, current

    def calculate_worst_case_power(
        self,
        component_id: str,
        failed_components: Optional[List[str]] = None
    ) -> float:
        """
        Calculate worst-case power at a component
        Considers max voltage and max current scenarios
        """
        if failed_components is None:
            failed_components = []

        component = self.circuit.components.get(component_id)
        if not component:
            return 0.0

        # Get all upstream sources
        upstream = self.circuit.get_upstream_components(component_id)
        sources = [s for s in self.circuit.get_sources() if s.id in upstream]

        if not sources:
            return 0.0

        # Worst case: maximum source voltage and current
        max_voltage = max((s.voltage_output for s in sources), default=0.0)
        max_current = sum((s.current_max for s in sources), default=0.0)

        # Apply component limits
        if component.voltage_max:
            max_voltage = min(max_voltage, component.voltage_max)
        if component.current_max:
            max_current = min(max_current, component.current_max)

        # Check protections
        if isinstance(component, ActiveComponent):
            max_voltage, max_current = self._apply_protections(
                component, max_voltage, max_current
            )

        return max_voltage * max_current

    def check_protections_active(
        self,
        state: CircuitState,
        component_id: str
    ) -> Dict[ProtectionType, bool]:
        """Check which protections would be triggered for a component"""
        component = self.circuit.components.get(component_id)
        if not isinstance(component, ActiveComponent):
            return {}

        voltage = state.get_voltage(component_id)
        current = state.get_current(component_id)
        power = state.get_power(component_id)

        triggered = {}

        for protection in component.protections:
            is_triggered = False

            if protection.type == ProtectionType.OVP:
                if protection.threshold_voltage and voltage > protection.threshold_voltage:
                    is_triggered = True

            elif protection.type == ProtectionType.UVP:
                if protection.threshold_voltage and voltage < protection.threshold_voltage:
                    is_triggered = True

            elif protection.type == ProtectionType.OCP:
                if protection.threshold_current and current > protection.threshold_current:
                    is_triggered = True

            elif protection.type == ProtectionType.FUSE:
                if protection.threshold_current and current > protection.threshold_current:
                    is_triggered = True

            elif protection.type == ProtectionType.CURRENT_LIMIT:
                if protection.threshold_current and current > protection.threshold_current:
                    is_triggered = True

            triggered[protection.type] = is_triggered

        return triggered
