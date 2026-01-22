"""
Circuit topology and network graph implementation
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
import networkx as nx

from .components import (
    Component, ActiveComponent, PassiveComponent, PowerSource, PowerSink,
    Connection, CircuitState, ComponentType
)


class Circuit:
    """Circuit topology representation"""

    def __init__(self, name: str = "Circuit"):
        self.name = name
        self.components: Dict[str, Component] = {}
        self.connections: List[Connection] = []
        self.graph = nx.DiGraph()  # Directed graph for power flow

    def add_component(self, component: Component) -> None:
        """Add a component to the circuit"""
        if component.id in self.components:
            raise ValueError(f"Component {component.id} already exists")

        self.components[component.id] = component
        self.graph.add_node(component.id, component=component)

    def add_connection(self, connection: Connection) -> None:
        """Add a connection between components"""
        if connection.from_component not in self.components:
            raise ValueError(f"Source component {connection.from_component} not found")
        if connection.to_component not in self.components:
            raise ValueError(f"Destination component {connection.to_component} not found")

        self.connections.append(connection)
        self.graph.add_edge(
            connection.from_component,
            connection.to_component,
            connection=connection,
            weight=connection.resistance
        )

    def attach_passive_to_active(self, passive_id: str, active_id: str) -> None:
        """Attach a passive component to an active component"""
        if passive_id not in self.components:
            raise ValueError(f"Passive component {passive_id} not found")
        if active_id not in self.components:
            raise ValueError(f"Active component {active_id} not found")

        passive = self.components[passive_id]
        active = self.components[active_id]

        if not passive.is_passive():
            raise ValueError(f"Component {passive_id} is not passive")
        if not isinstance(active, ActiveComponent):
            raise ValueError(f"Component {active_id} is not active")

        active.attached_passives.append(passive_id)

    def get_sources(self) -> List[PowerSource]:
        """Get all power sources in the circuit"""
        return [c for c in self.components.values() if c.is_source()]

    def get_sinks(self) -> List[PowerSink]:
        """Get all power sinks in the circuit"""
        return [c for c in self.components.values() if c.is_sink()]

    def get_active_components(self) -> List[ActiveComponent]:
        """Get all active components"""
        return [c for c in self.components.values() if isinstance(c, ActiveComponent)]

    def get_passive_components(self) -> List[PassiveComponent]:
        """Get all passive components"""
        return [c for c in self.components.values() if isinstance(c, PassiveComponent)]

    def get_certified_components(self) -> List[ActiveComponent]:
        """Get certified active components"""
        return [c for c in self.get_active_components() if c.certified]

    def get_non_certified_components(self) -> List[ActiveComponent]:
        """Get non-certified active components"""
        return [c for c in self.get_active_components() if not c.certified]

    def find_paths(self, source_id: str, sink_id: str) -> List[List[str]]:
        """Find all paths from source to sink"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source_id, sink_id))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def find_all_paths(self) -> List[List[str]]:
        """Find all paths from sources to sinks"""
        all_paths = []
        sources = self.get_sources()
        sinks = self.get_sinks()

        for source in sources:
            for sink in sinks:
                paths = self.find_paths(source.id, sink.id)
                all_paths.extend(paths)

        return all_paths

    def get_path_components(self, path: List[str]) -> List[Component]:
        """Get component objects for a path"""
        return [self.components[comp_id] for comp_id in path]

    def get_downstream_components(self, component_id: str) -> Set[str]:
        """Get all components downstream from given component"""
        if component_id not in self.graph:
            return set()

        downstream = set()
        visited = set()
        queue = deque([component_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for successor in self.graph.successors(current):
                downstream.add(successor)
                queue.append(successor)

        return downstream

    def get_upstream_components(self, component_id: str) -> Set[str]:
        """Get all components upstream from given component"""
        if component_id not in self.graph:
            return set()

        upstream = set()
        visited = set()
        queue = deque([component_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for predecessor in self.graph.predecessors(current):
                upstream.add(predecessor)
                queue.append(predecessor)

        return upstream

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate circuit topology
        Returns (is_valid, list_of_errors)
        """
        errors = []

        # Check for at least one source and one sink
        if len(self.get_sources()) == 0:
            errors.append("Circuit has no power sources")

        if len(self.get_sinks()) == 0:
            errors.append("Circuit has no power sinks")

        # Check for disconnected components
        if not nx.is_weakly_connected(self.graph):
            errors.append("Circuit has disconnected components")

        # Check for cycles (which might indicate design issues)
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            errors.append(f"Circuit contains {len(cycles)} cycle(s)")

        # Validate passive components are attached to active components
        for passive in self.get_passive_components():
            # Check if passive is in any active component's attached list
            is_attached = False
            for active in self.get_active_components():
                if passive.id in active.attached_passives:
                    is_attached = True
                    break

            if not is_attached:
                errors.append(
                    f"Passive component {passive.id} is not attached to any active component"
                )

        return len(errors) == 0, errors

    def __str__(self):
        return (
            f"Circuit: {self.name}\n"
            f"  Components: {len(self.components)}\n"
            f"  Connections: {len(self.connections)}\n"
            f"  Sources: {len(self.get_sources())}\n"
            f"  Sinks: {len(self.get_sinks())}\n"
            f"  Active: {len(self.get_active_components())}\n"
            f"  Passive: {len(self.get_passive_components())}"
        )
