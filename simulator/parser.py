"""
Circuit definition parser
Supports JSON and dictionary-based circuit definitions
"""

import json
from typing import Dict, Any, List

from .components import (
    Component, ActiveComponent, PassiveComponent, PowerSource, PowerSink,
    ComponentType, Protection, ProtectionType, Connection
)
from .circuit import Circuit


class CircuitParser:
    """Parse circuit definitions from various formats"""

    @staticmethod
    def from_dict(circuit_def: Dict[str, Any]) -> Circuit:
        """
        Parse circuit from dictionary definition

        Expected format:
        {
            "name": "Circuit Name",
            "components": [...],
            "connections": [...],
            "attachments": [...]
        }
        """
        circuit = Circuit(name=circuit_def.get("name", "Circuit"))

        # Parse components
        for comp_def in circuit_def.get("components", []):
            component = CircuitParser._parse_component(comp_def)
            circuit.add_component(component)

        # Parse connections
        for conn_def in circuit_def.get("connections", []):
            connection = CircuitParser._parse_connection(conn_def)
            circuit.add_connection(connection)

        # Parse passive-to-active attachments
        for attach_def in circuit_def.get("attachments", []):
            passive_id = attach_def["passive"]
            active_id = attach_def["active"]
            circuit.attach_passive_to_active(passive_id, active_id)

        return circuit

    @staticmethod
    def from_json(json_str: str) -> Circuit:
        """Parse circuit from JSON string"""
        circuit_def = json.loads(json_str)
        return CircuitParser.from_dict(circuit_def)

    @staticmethod
    def from_json_file(filepath: str) -> Circuit:
        """Parse circuit from JSON file"""
        with open(filepath, 'r') as f:
            circuit_def = json.load(f)
        return CircuitParser.from_dict(circuit_def)

    @staticmethod
    def _parse_component(comp_def: Dict[str, Any]) -> Component:
        """Parse a single component from definition"""
        comp_type = ComponentType(comp_def["type"])
        comp_id = comp_def["id"]
        name = comp_def.get("name", comp_id)

        # Common properties
        common_props = {
            "id": comp_id,
            "component_type": comp_type,
            "name": name,
            "voltage_nominal": comp_def.get("voltage_nominal"),
            "voltage_min": comp_def.get("voltage_min"),
            "voltage_max": comp_def.get("voltage_max"),
            "current_nominal": comp_def.get("current_nominal"),
            "current_min": comp_def.get("current_min"),
            "current_max": comp_def.get("current_max"),
            "power_rating": comp_def.get("power_rating")
        }

        # Create appropriate component type
        if comp_type in [ComponentType.ADAPTER, ComponentType.BATTERY]:
            return PowerSource(
                **common_props,
                voltage_output=comp_def.get("voltage_output", 0.0),
                current_max=comp_def.get("current_max", 0.0),
                power_max=comp_def.get("power_max", 0.0)
            )

        elif comp_type == ComponentType.SINK:
            return PowerSink(
                **common_props,
                power_consumption=comp_def.get("power_consumption", 0.0),
                voltage_required=comp_def.get("voltage_required", 0.0),
                current_required=comp_def.get("current_required", 0.0)
            )

        elif comp_type in [ComponentType.IC, ComponentType.FET, ComponentType.LDO,
                          ComponentType.DCDC, ComponentType.PMU]:
            # Parse protections
            protections = []
            for prot_def in comp_def.get("protections", []):
                protection = CircuitParser._parse_protection(prot_def)
                protections.append(protection)

            return ActiveComponent(
                **common_props,
                certified=comp_def.get("certified", False),
                protections=protections,
                efficiency=comp_def.get("efficiency")
            )

        else:  # Passive components
            return PassiveComponent(
                **common_props,
                resistance=comp_def.get("resistance"),
                capacitance=comp_def.get("capacitance"),
                inductance=comp_def.get("inductance"),
                forward_voltage=comp_def.get("forward_voltage")
            )

    @staticmethod
    def _parse_protection(prot_def: Dict[str, Any]) -> Protection:
        """Parse protection mechanism"""
        return Protection(
            type=ProtectionType(prot_def["type"]),
            threshold_voltage=prot_def.get("threshold_voltage"),
            threshold_current=prot_def.get("threshold_current"),
            threshold_temperature=prot_def.get("threshold_temperature"),
            threshold_power=prot_def.get("threshold_power"),
            response_time=prot_def.get("response_time")
        )

    @staticmethod
    def _parse_connection(conn_def: Dict[str, Any]) -> Connection:
        """Parse connection"""
        return Connection(
            from_component=conn_def["from"],
            to_component=conn_def["to"],
            connection_type=conn_def.get("type", "power"),
            resistance=conn_def.get("resistance", 0.0)
        )

    @staticmethod
    def to_dict(circuit: Circuit) -> Dict[str, Any]:
        """Convert circuit to dictionary format"""
        components = []
        for comp in circuit.components.values():
            comp_dict = {
                "id": comp.id,
                "type": comp.component_type.value,
                "name": comp.name
            }

            # Add type-specific fields
            if isinstance(comp, PowerSource):
                comp_dict.update({
                    "voltage_output": comp.voltage_output,
                    "current_max": comp.current_max,
                    "power_max": comp.power_max
                })
            elif isinstance(comp, PowerSink):
                comp_dict.update({
                    "power_consumption": comp.power_consumption,
                    "voltage_required": comp.voltage_required,
                    "current_required": comp.current_required
                })
            elif isinstance(comp, ActiveComponent):
                comp_dict.update({
                    "certified": comp.certified,
                    "efficiency": comp.efficiency,
                    "protections": [
                        {
                            "type": p.type.value,
                            "threshold_voltage": p.threshold_voltage,
                            "threshold_current": p.threshold_current,
                            "threshold_temperature": p.threshold_temperature,
                            "threshold_power": p.threshold_power
                        }
                        for p in comp.protections
                    ]
                })

            components.append(comp_dict)

        connections = [
            {
                "from": conn.from_component,
                "to": conn.to_component,
                "type": conn.connection_type,
                "resistance": conn.resistance
            }
            for conn in circuit.connections
        ]

        # Extract attachments
        attachments = []
        for active in circuit.get_active_components():
            for passive_id in active.attached_passives:
                attachments.append({
                    "passive": passive_id,
                    "active": active.id
                })

        return {
            "name": circuit.name,
            "components": components,
            "connections": connections,
            "attachments": attachments
        }

    @staticmethod
    def to_json(circuit: Circuit, indent: int = 2) -> str:
        """Convert circuit to JSON string"""
        return json.dumps(CircuitParser.to_dict(circuit), indent=indent)
