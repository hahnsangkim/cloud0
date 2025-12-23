#!/usr/bin/env python3
"""
cloud0 - Multi-cloud status checker
Monitors the operational status of major cloud service providers
"""

import argparse
import json
import sys
from typing import Dict, Optional
import requests


class CloudStatusChecker:
    """Check the status of various cloud providers"""

    PROVIDERS = {
        'aws': {
            'name': 'AWS',
            'url': 'https://status.aws.amazon.com/',
            'api': 'https://status.aws.amazon.com/data.json'
        },
        'azure': {
            'name': 'Azure',
            'url': 'https://status.azure.com/en-us/status',
            'api': 'https://status.azure.com/en-us/status/feed/'
        },
        'gcp': {
            'name': 'GCP',
            'url': 'https://status.cloud.google.com/',
            'api': 'https://status.cloud.google.com/incidents.json'
        },
        'digitalocean': {
            'name': 'DigitalOcean',
            'url': 'https://status.digitalocean.com/',
            'api': 'https://s2k7tnzlhrpw.statuspage.io/api/v2/status.json'
        },
        'cloudflare': {
            'name': 'Cloudflare',
            'url': 'https://www.cloudflarestatus.com/',
            'api': 'https://yh6f0r4529hb.statuspage.io/api/v2/status.json'
        }
    }

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'cloud0/1.0 (Cloud Status Checker)'
        })

    def check_statuspage_io(self, api_url: str) -> Dict[str, str]:
        """Check status for statuspage.io based providers"""
        try:
            response = self.session.get(api_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            status = data.get('status', {})
            indicator = status.get('indicator', 'unknown')
            description = status.get('description', 'Unknown')

            if indicator == 'none':
                return {'status': 'operational', 'message': description}
            elif indicator in ['minor', 'major', 'critical']:
                return {'status': 'degraded', 'message': description}
            else:
                return {'status': 'unknown', 'message': description}

        except requests.RequestException as e:
            return {'status': 'error', 'message': f'Failed to fetch status: {str(e)}'}

    def check_aws(self) -> Dict[str, str]:
        """Check AWS status"""
        return self.check_generic_status('aws')

    def check_azure(self) -> Dict[str, str]:
        """Check Azure status"""
        return self.check_generic_status('azure')

    def check_gcp(self) -> Dict[str, str]:
        """Check GCP status"""
        try:
            response = self.session.get(self.PROVIDERS['gcp']['api'], timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # If there are no active incidents, service is operational
            if not data or len(data) == 0:
                return {'status': 'operational', 'message': 'All services operational'}

            # Check for ongoing incidents
            ongoing = [inc for inc in data if inc.get('end') is None or inc.get('end') == '']
            if ongoing:
                return {'status': 'degraded', 'message': f'{len(ongoing)} active incident(s)'}

            return {'status': 'operational', 'message': 'All services operational'}

        except requests.RequestException as e:
            return {'status': 'error', 'message': f'Failed to fetch status: {str(e)}'}

    def check_digitalocean(self) -> Dict[str, str]:
        """Check DigitalOcean status"""
        return self.check_statuspage_io(self.PROVIDERS['digitalocean']['api'])

    def check_cloudflare(self) -> Dict[str, str]:
        """Check Cloudflare status"""
        return self.check_statuspage_io(self.PROVIDERS['cloudflare']['api'])

    def check_generic_status(self, provider: str) -> Dict[str, str]:
        """Generic status check that attempts HTTP request"""
        try:
            url = self.PROVIDERS[provider]['url']
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # If we can reach the page, assume operational
            return {'status': 'operational', 'message': 'Service reachable'}

        except requests.RequestException as e:
            return {'status': 'error', 'message': f'Failed to reach service: {str(e)}'}

    def check_provider(self, provider: str) -> Optional[Dict[str, str]]:
        """Check status for a specific provider"""
        if provider not in self.PROVIDERS:
            return None

        check_method = getattr(self, f'check_{provider}', None)
        if check_method:
            result = check_method()
        else:
            result = self.check_generic_status(provider)

        result['provider'] = self.PROVIDERS[provider]['name']
        result['url'] = self.PROVIDERS[provider]['url']
        return result

    def check_all(self) -> Dict[str, Dict[str, str]]:
        """Check status for all providers"""
        results = {}
        for provider_key in self.PROVIDERS:
            results[provider_key] = self.check_provider(provider_key)
        return results


def format_status_symbol(status: str) -> str:
    """Return a symbol representing the status"""
    symbols = {
        'operational': '✓',
        'degraded': '⚠',
        'error': '✗',
        'unknown': '?'
    }
    return symbols.get(status, '?')


def format_status_color(status: str, text: str) -> str:
    """Add color codes to status text (if terminal supports it)"""
    colors = {
        'operational': '\033[92m',  # Green
        'degraded': '\033[93m',     # Yellow
        'error': '\033[91m',        # Red
        'unknown': '\033[90m'       # Gray
    }
    reset = '\033[0m'

    if sys.stdout.isatty():
        color = colors.get(status, '')
        return f'{color}{text}{reset}'
    return text


def print_results(results: Dict[str, Dict[str, str]], json_output: bool = False):
    """Print the status check results"""
    if json_output:
        print(json.dumps(results, indent=2))
        return

    print("\nCloud Provider Status Check")
    print("=" * 50)
    print()

    for provider_key, result in results.items():
        if result:
            status = result['status']
            provider_name = result['provider']
            message = result.get('message', '')

            symbol = format_status_symbol(status)
            status_text = status.capitalize()

            # Format with color
            colored_symbol = format_status_color(status, symbol)
            colored_status = format_status_color(status, status_text)

            print(f"{provider_name:18} {colored_symbol} {colored_status}")

            if message and status != 'operational':
                print(f"  └─ {message}")

    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Check the operational status of cloud service providers'
    )
    parser.add_argument(
        '--provider',
        choices=list(CloudStatusChecker.PROVIDERS.keys()),
        help='Check specific provider only'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        help='Request timeout in seconds (default: 5)'
    )

    args = parser.parse_args()

    checker = CloudStatusChecker(timeout=args.timeout)

    if args.provider:
        result = checker.check_provider(args.provider)
        if result:
            results = {args.provider: result}
        else:
            print(f"Error: Unknown provider '{args.provider}'", file=sys.stderr)
            sys.exit(1)
    else:
        results = checker.check_all()

    print_results(results, json_output=args.json)

    # Exit with error code if any provider is not operational
    if any(r and r['status'] != 'operational' for r in results.values()):
        sys.exit(1)


if __name__ == '__main__':
    main()
