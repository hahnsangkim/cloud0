"""
Safety analysis reporting and visualization
"""

import json
from typing import Dict, List, Any
from tabulate import tabulate

from .components import SafetyLevel
from .fault_simulator import SafetyViolation, FaultCondition


class SafetyReporter:
    """Generate safety analysis reports"""

    @staticmethod
    def generate_text_report(analysis_results: Dict) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("IEC 62368-1 ELECTRICAL SAFETY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Scenarios Tested: {analysis_results['total_scenarios']}")
        lines.append(f"Total Violations Found: {analysis_results['total_violations']}")
        lines.append(f"Critical Paths Found: {len(analysis_results['critical_paths'])}")
        lines.append(f"Safety Status: {'FAIL' if analysis_results['has_safety_issues'] else 'PASS'}")
        lines.append("")

        # Scenario breakdown
        lines.append("SCENARIO ANALYSIS")
        lines.append("-" * 80)

        scenario_table = []
        for result in analysis_results['scenario_results']:
            scenario = result['scenario']
            scenario_table.append([
                scenario.condition_type.value,
                len(scenario.failed_components),
                result['violation_count'],
                scenario.description
            ])

        lines.append(tabulate(
            scenario_table,
            headers=['Condition', 'Failed Components', 'Violations', 'Description'],
            tablefmt='grid'
        ))
        lines.append("")

        # Violations details
        if analysis_results['violations']:
            lines.append("SAFETY VIOLATIONS")
            lines.append("-" * 80)

            for i, violation in enumerate(analysis_results['violations'], 1):
                lines.append(f"\nViolation #{i}")
                lines.append(f"  Component: {violation.component_name} ({violation.component_id})")
                lines.append(f"  Power: {violation.power:.2f}W")
                lines.append(f"  Safety Level: {violation.safety_level.value}")
                lines.append(f"  Voltage: {violation.voltage:.2f}V")
                lines.append(f"  Current: {violation.current:.2f}A")
                lines.append(f"  Fault Condition: {violation.fault_scenario.condition_type.value}")
                lines.append(f"  Scenario: {violation.fault_scenario.description}")
                lines.append(f"  Has Protection: {'Yes' if violation.has_protection else 'No'}")
                if violation.protection_details:
                    lines.append(f"  Protection Details: {violation.protection_details}")
        else:
            lines.append("SAFETY VIOLATIONS")
            lines.append("-" * 80)
            lines.append("No safety violations detected.")
            lines.append("")

        # Critical paths
        if analysis_results['critical_paths']:
            lines.append("\nCRITICAL PATHS")
            lines.append("-" * 80)

            for i, path_info in enumerate(analysis_results['critical_paths'], 1):
                lines.append(f"\nCritical Path #{i}")
                path_names = ' -> '.join(path_info['path_names'])
                lines.append(f"  Path: {path_names}")
                lines.append(f"  Condition: {path_info['scenario'].condition_type.value}")
                lines.append(f"  Scenario: {path_info['scenario'].description}")
                violation = path_info['violation']
                lines.append(f"  Violation Power: {violation.power:.2f}W ({violation.safety_level.value})")
                lines.append(f"  Protected: {'Yes' if path_info['protected'] else 'No'}")
        else:
            lines.append("\nCRITICAL PATHS")
            lines.append("-" * 80)
            lines.append("No critical paths detected.")

        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return '\n'.join(lines)

    @staticmethod
    def generate_json_report(analysis_results: Dict) -> str:
        """Generate JSON report"""
        # Convert objects to serializable format
        report = {
            'summary': {
                'total_scenarios': analysis_results['total_scenarios'],
                'total_violations': analysis_results['total_violations'],
                'critical_paths_count': len(analysis_results['critical_paths']),
                'has_safety_issues': analysis_results['has_safety_issues']
            },
            'scenarios': [],
            'violations': [],
            'critical_paths': []
        }

        # Scenarios
        for result in analysis_results['scenario_results']:
            scenario = result['scenario']
            report['scenarios'].append({
                'condition_type': scenario.condition_type.value,
                'failed_components': scenario.failed_components,
                'description': scenario.description,
                'violation_count': result['violation_count']
            })

        # Violations
        for violation in analysis_results['violations']:
            report['violations'].append({
                'component_id': violation.component_id,
                'component_name': violation.component_name,
                'power': violation.power,
                'voltage': violation.voltage,
                'current': violation.current,
                'safety_level': violation.safety_level.value,
                'condition_type': violation.fault_scenario.condition_type.value,
                'scenario_description': violation.fault_scenario.description,
                'has_protection': violation.has_protection,
                'protection_details': violation.protection_details
            })

        # Critical paths
        for path_info in analysis_results['critical_paths']:
            violation = path_info['violation']
            report['critical_paths'].append({
                'path': path_info['path'],
                'path_names': path_info['path_names'],
                'condition_type': path_info['scenario'].condition_type.value,
                'scenario_description': path_info['scenario'].description,
                'violation_power': violation.power,
                'violation_safety_level': violation.safety_level.value,
                'protected': path_info['protected']
            })

        return json.dumps(report, indent=2)

    @staticmethod
    def generate_summary(analysis_results: Dict) -> str:
        """Generate brief summary"""
        status = "PASS" if not analysis_results['has_safety_issues'] else "FAIL"
        return (
            f"Safety Analysis: {status}\n"
            f"Scenarios: {analysis_results['total_scenarios']}, "
            f"Violations: {analysis_results['total_violations']}, "
            f"Critical Paths: {len(analysis_results['critical_paths'])}"
        )
