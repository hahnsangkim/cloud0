#!/usr/bin/env python3
"""
Electrical Circuit Safety Simulator - Main CLI
IEC 62368-1 Compliance Analysis Tool
"""

import argparse
import sys
from pathlib import Path

from simulator import (
    Circuit, CircuitParser, FaultSimulator, SafetyReporter
)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='IEC 62368-1 Electrical Circuit Safety Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze circuit from JSON file
  python safety_simulator.py circuit.json

  # Generate JSON output
  python safety_simulator.py circuit.json --json

  # Save report to file
  python safety_simulator.py circuit.json --output report.txt

  # Validate circuit without full analysis
  python safety_simulator.py circuit.json --validate-only

Safety Levels (IEC 62368-1):
  P1: Power <= 15W (Safe)
  P2: Power > 15W and <= 100W (Safety violation)
  P3: Power > 100W (Critical safety violation)
        """
    )

    parser.add_argument(
        'circuit_file',
        type=str,
        help='Path to circuit definition file (JSON format)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output report in JSON format'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save report to file instead of stdout'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate circuit topology without running safety analysis'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show brief summary only'
    )

    args = parser.parse_args()

    # Load circuit
    try:
        print(f"Loading circuit from {args.circuit_file}...", file=sys.stderr)
        circuit = CircuitParser.from_json_file(args.circuit_file)
        print(f"Circuit loaded: {circuit.name}", file=sys.stderr)
        print(circuit, file=sys.stderr)
        print("", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Circuit file '{args.circuit_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading circuit: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate circuit
    print("Validating circuit topology...", file=sys.stderr)
    is_valid, errors = circuit.validate()

    if not is_valid:
        print("Circuit validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        if not args.validate_only:
            print("\nProceeding with analysis despite validation errors...", file=sys.stderr)
            print("", file=sys.stderr)
    else:
        print("Circuit topology valid.", file=sys.stderr)
        print("", file=sys.stderr)

    if args.validate_only:
        sys.exit(0 if is_valid else 1)

    # Run safety analysis
    print("Running IEC 62368-1 safety analysis...", file=sys.stderr)
    simulator = FaultSimulator(circuit)
    analysis_results = simulator.run_full_analysis()
    print(f"Analysis complete. Found {analysis_results['total_violations']} violations.", file=sys.stderr)
    print("", file=sys.stderr)

    # Generate report
    if args.json:
        report = SafetyReporter.generate_json_report(analysis_results)
    elif args.summary:
        report = SafetyReporter.generate_summary(analysis_results)
    else:
        report = SafetyReporter.generate_text_report(analysis_results)

    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(report)

    # Exit with appropriate code
    sys.exit(1 if analysis_results['has_safety_issues'] else 0)


if __name__ == '__main__':
    main()
