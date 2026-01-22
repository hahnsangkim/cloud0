# cloud0 - Electrical Circuit Safety Simulator

An IEC 62368-1 compliant electrical circuit safety simulator that identifies critical paths causing safety integrity breaches in power distribution networks.

## Overview

The simulator analyzes electrical circuit topologies under normal, abnormal, and single-fault conditions to identify safety violations according to IEC 62368-1 power level classifications:

- **P1**: ≤ 15W (Safe)
- **P2**: > 15W and ≤ 100W (Safety violation)
- **P3**: > 100W (Critical safety violation)

## Features

- **Component Modeling**: Support for passive (resistors, capacitors, inductors, diodes) and active components (ICs, FETs, LDOs, DC-DCs, PMUs)
- **Topology Analysis**: Network graph-based circuit topology with power source to sink path analysis
- **Safeguard Simulation**: Models protection mechanisms (OVP, OCP, OTP, UVP, UTP, current limits, fuses)
- **Fault Conditions**: Simulates normal, single-fault (certified component passives), and abnormal (non-certified component) conditions
- **Critical Path Detection**: Identifies power paths that violate safety integrity
- **Comprehensive Reporting**: Text and JSON reports with detailed violation analysis

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Define Your Circuit

Create a JSON file describing your circuit (see `examples/` directory):

```json
{
  "name": "My Circuit",
  "components": [
    {
      "id": "adapter1",
      "type": "adapter",
      "voltage_output": 12.0,
      "current_max": 2.0
    },
    {
      "id": "ldo1",
      "type": "ldo",
      "certified": true,
      "voltage_nominal": 5.0,
      "protections": [
        {
          "type": "over_current_protection",
          "threshold_current": 1.5
        }
      ]
    }
  ],
  "connections": [
    {"from": "adapter1", "to": "ldo1"}
  ]
}
```

### 2. Run Safety Analysis

```bash
python safety_simulator.py examples/simple_safe_circuit.json
```

### 3. Review Results

The simulator will generate a detailed report showing:
- Safety violations (P2/P3 power levels)
- Critical paths from source to sink
- Protection mechanism effectiveness
- Fault scenario analysis

## Usage

### Basic Analysis

```bash
python safety_simulator.py circuit.json
```

### JSON Output

```bash
python safety_simulator.py circuit.json --json
```

### Save Report

```bash
python safety_simulator.py circuit.json --output report.txt
```

### Validate Circuit Only

```bash
python safety_simulator.py circuit.json --validate-only
```

### Brief Summary

```bash
python safety_simulator.py circuit.json --summary
```

## Component Types

### Power Sources
- **Adapter**: DC power adapter with voltage/current/power ratings
- **Battery**: Battery source with capacity specifications

### Active Components (Main Network)
- **IC**: Integrated circuit
- **FET**: Field-effect transistor
- **LDO**: Low-dropout regulator
- **DCDC**: DC-DC converter
- **PMU**: Power management unit

Active components can be:
- **Certified**: Non-safety-violent failures only
- **Non-certified**: Can result in safety-violent failures

### Passive Components (Attached to Active)
- **Resistor**: Current sensing, voltage division
- **Capacitor**: Energy storage, filtering
- **Inductor**: Energy storage, filtering
- **Diode**: Rectification, protection

### Power Sinks
- **Sink**: Function endpoint consuming power

## Protection Mechanisms (Safeguards)

Components can have the following protections:

- **OVP** (Over-Voltage Protection): Cuts power if voltage exceeds threshold
- **OCP** (Over-Current Protection): Cuts power if current exceeds threshold
- **OTP** (Over-Temperature Protection): Cuts power if temperature exceeds threshold
- **UVP** (Under-Voltage Protection): Cuts power if voltage below threshold
- **UTP** (Under-Temperature Protection): Cuts power if temperature below threshold
- **Current Limit**: Enforces maximum current (soft limit)
- **Fuse**: Permanently opens if current exceeds threshold

## Fault Conditions (IEC 62368-1)

### Normal Condition
- No component failures
- All components operating within specifications

### Single-Fault Condition
- Passive components attached to **certified** active components fail
- Tests robustness of certified components

### Abnormal Condition
- **Non-certified** active components fail, OR
- Passive components attached to non-certified components fail
- Tests worst-case scenarios with uncertified parts

## Architecture

```
simulator/
├── components.py       # Component models and data structures
├── circuit.py          # Circuit topology and network graph
├── power_analysis.py   # Power flow calculation engine
├── fault_simulator.py  # Fault condition simulation
├── parser.py           # JSON circuit definition parser
└── reporter.py         # Report generation
```

## Examples

See the `examples/` directory for sample circuits:

1. **simple_safe_circuit.json**: Low-power certified circuit with protections
2. **unsafe_circuit.json**: High-power non-certified circuit without adequate protections
3. **protected_high_power.json**: High-power circuit with comprehensive protections

## Exit Codes

- `0`: No safety violations detected
- `1`: Safety violations or critical paths found

## Requirements

- Python 3.7+
- networkx >= 3.0
- tabulate >= 0.9.0

## License

MIT
