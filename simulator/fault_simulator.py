"""
Fault condition simulator for safety analysis
IEC 62368-1 normal, abnormal, and single-fault conditions
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from itertools import combinations

from .components import (
    Component, ActiveComponent, PassiveComponent, CircuitState, SafetyLevel
)
from .circuit import Circuit
from .power_analysis import PowerFlowAnalyzer


class FaultCondition(Enum):
    """Types of fault conditions per IEC 62368-1"""
    NORMAL = "normal"  # No faults
    SINGLE_FAULT = "single_fault"  # Passive components on certified active fail
    ABNORMAL = "abnormal"  # Non-certified components or their passives fail


@dataclass
class FaultScenario:
    """Represents a fault scenario"""
    condition_type: FaultCondition
    failed_components: List[str]
    description: str

    def __str__(self):
        return f"{self.condition_type.value}: {self.description}"


@dataclass
class SafetyViolation:
    """Represents a safety integrity violation"""
    component_id: str
    component_name: str
    power: float
    voltage: float
    current: float
    safety_level: SafetyLevel
    fault_scenario: FaultScenario
    path: Optional[List[str]] = None
    has_protection: bool = False
    protection_details: str = ""

    def __str__(self):
        return (
            f"Safety Violation at {self.component_name} ({self.component_id})\n"
            f"  Power: {self.power:.2f}W ({self.safety_level.value})\n"
            f"  Voltage: {self.voltage:.2f}V, Current: {self.current:.2f}A\n"
            f"  Scenario: {self.fault_scenario}\n"
            f"  Protected: {self.has_protection}"
        )


class FaultSimulator:
    """Simulate fault conditions and detect safety violations"""

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.analyzer = PowerFlowAnalyzer(circuit)

    def generate_fault_scenarios(self) -> List[FaultScenario]:
        """
        Generate all relevant fault scenarios according to IEC 62368-1

        1. Normal condition: No faults
        2. Single-fault condition: Passive components attached to certified active components fail
        3. Abnormal condition: Non-certified active components fail, or their passive components fail
        """
        scenarios = []

        # Normal condition
        scenarios.append(FaultScenario(
            condition_type=FaultCondition.NORMAL,
            failed_components=[],
            description="Normal operation - no faults"
        ))

        # Single-fault conditions
        certified_actives = self.circuit.get_certified_components()

        for active in certified_actives:
            for passive_id in active.attached_passives:
                passive = self.circuit.components.get(passive_id)
                if passive:
                    scenarios.append(FaultScenario(
                        condition_type=FaultCondition.SINGLE_FAULT,
                        failed_components=[passive_id],
                        description=f"Single fault: {passive.name} attached to certified {active.name} fails"
                    ))

        # Abnormal conditions - non-certified active components fail
        non_certified_actives = self.circuit.get_non_certified_components()

        for active in non_certified_actives:
            # Active component itself fails
            scenarios.append(FaultScenario(
                condition_type=FaultCondition.ABNORMAL,
                failed_components=[active.id],
                description=f"Abnormal: Non-certified {active.name} fails"
            ))

            # Passive components attached to non-certified active fail
            for passive_id in active.attached_passives:
                passive = self.circuit.components.get(passive_id)
                if passive:
                    scenarios.append(FaultScenario(
                        condition_type=FaultCondition.ABNORMAL,
                        failed_components=[passive_id],
                        description=f"Abnormal: {passive.name} attached to non-certified {active.name} fails"
                    ))

        return scenarios

    def simulate_scenario(self, scenario: FaultScenario) -> CircuitState:
        """Simulate a fault scenario and return circuit state"""
        return self.analyzer.calculate_power_flow(
            failed_components=scenario.failed_components
        )

    def check_safety_violations(
        self,
        scenario: FaultScenario,
        state: CircuitState
    ) -> List[SafetyViolation]:
        """
        Check for safety integrity violations in the circuit state

        IEC 62368-1 violation criteria:
        - P2: Power > 15W
        - P3: Power > 100W
        """
        violations = []

        for comp_id, power in state.power_map.items():
            # Check if power exceeds P1 level (15W)
            if not state.is_safety_violation(power):
                continue

            component = self.circuit.components[comp_id]
            safety_level = state.classify_safety_level(power)

            # Check if component has protections that would prevent violation
            has_protection = False
            protection_details = ""

            if isinstance(component, ActiveComponent):
                protections_triggered = self.analyzer.check_protections_active(state, comp_id)
                if any(protections_triggered.values()):
                    has_protection = True
                    triggered_types = [
                        ptype.value for ptype, triggered in protections_triggered.items()
                        if triggered
                    ]
                    protection_details = f"Triggered: {', '.join(triggered_types)}"

            violation = SafetyViolation(
                component_id=comp_id,
                component_name=component.name,
                power=power,
                voltage=state.get_voltage(comp_id),
                current=state.get_current(comp_id),
                safety_level=safety_level,
                fault_scenario=scenario,
                has_protection=has_protection,
                protection_details=protection_details
            )

            violations.append(violation)

        return violations

    def find_critical_paths(self) -> List[Dict]:
        """
        Find critical paths that can lead to safety violations

        A critical path is a path from source to sink where a fault
        condition can cause power to exceed safety limits without
        adequate protection.
        """
        critical_paths = []

        # Get all scenarios
        scenarios = self.generate_fault_scenarios()

        # For each scenario, simulate and check violations
        for scenario in scenarios:
            state = self.simulate_scenario(scenario)
            violations = self.check_safety_violations(scenario, state)

            # For each violation, find the path(s) that contribute
            for violation in violations:
                # Find all paths that include this component
                all_paths = self.circuit.find_all_paths()

                for path in all_paths:
                    if violation.component_id in path:
                        # Check if this path has adequate protections
                        path_components = self.circuit.get_path_components(path)
                        has_adequate_protection = self._check_path_protection(
                            path_components, violation
                        )

                        if not has_adequate_protection:
                            critical_paths.append({
                                'path': path,
                                'path_names': [self.circuit.components[cid].name for cid in path],
                                'violation': violation,
                                'scenario': scenario,
                                'protected': False
                            })

        return critical_paths

    def _check_path_protection(
        self,
        path_components: List[Component],
        violation: SafetyViolation
    ) -> bool:
        """Check if a path has adequate protection against violation"""

        # Check if any component in path has protection that would prevent this violation
        for component in path_components:
            if not isinstance(component, ActiveComponent):
                continue

            # Check for relevant protections
            protections = component.protections

            for protection in protections:
                # Over-power protection via current/voltage limits
                if protection.threshold_current:
                    safe_power = violation.voltage * protection.threshold_current
                    if safe_power <= 15.0:  # Within P1 limits
                        return True

                if protection.threshold_voltage:
                    safe_power = protection.threshold_voltage * violation.current
                    if safe_power <= 15.0:
                        return True

        return False

    def run_full_analysis(self) -> Dict:
        """
        Run complete safety analysis

        Returns:
            Dictionary with analysis results including scenarios, violations, and critical paths
        """
        scenarios = self.generate_fault_scenarios()
        all_violations = []
        scenario_results = []

        for scenario in scenarios:
            state = self.simulate_scenario(scenario)
            violations = self.check_safety_violations(scenario, state)

            scenario_results.append({
                'scenario': scenario,
                'state': state,
                'violations': violations,
                'violation_count': len(violations)
            })

            all_violations.extend(violations)

        critical_paths = self.find_critical_paths()

        return {
            'total_scenarios': len(scenarios),
            'scenario_results': scenario_results,
            'total_violations': len(all_violations),
            'violations': all_violations,
            'critical_paths': critical_paths,
            'has_safety_issues': len(all_violations) > 0 or len(critical_paths) > 0
        }
