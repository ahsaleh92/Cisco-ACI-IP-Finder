#!/usr/bin/env python3
"""
Cisco ACI IP Finder
A tool to discover and find IP addresses in Cisco ACI environments.
"""

import sys
import json
import argparse
import requests
import urllib3
from urllib.parse import urlparse
import logging
from typing import Dict, List, Optional, Tuple

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ACIIPFinder:
    """Main class for Cisco ACI IP discovery operations."""
    
    def __init__(self, apic_url: str, username: str, password: str, verify_ssl: bool = False):
        """Initialize the ACI IP Finder.
        
        Args:
            apic_url: URL of the APIC controller
            username: Username for authentication
            password: Password for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.apic_url = apic_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self) -> bool:
        """Authenticate with the APIC controller.
        
        Returns:
            True if authentication successful, False otherwise
        """
        auth_url = f"{self.apic_url}/api/aaaLogin.json"
        auth_data = {
            "aaaUser": {
                "attributes": {
                    "name": self.username,
                    "pwd": self.password
                }
            }
        }
        
        try:
            response = self.session.post(
                auth_url,
                json=auth_data,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            # Extract token from response
            auth_response = response.json()
            self.token = auth_response['imdata'][0]['aaaLogin']['attributes']['token']
            
            # Set token in session headers
            self.session.headers.update({
                'APIC-Cookie': f'APIC-cookie={self.token}'
            })
            
            logger.info("Successfully authenticated with APIC")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract authentication token: {e}")
            return False
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make an authenticated API request to APIC.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            JSON response data or None if request failed
        """
        if not self.token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None
            
        url = f"{self.apic_url}/api/{endpoint}"
        
        try:
            response = self.session.get(
                url,
                params=params,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None
    
    def find_all_endpoints(self) -> List[Dict]:
        """Find all endpoints (IP addresses) in the ACI fabric.
        
        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering all endpoints...")
        
        endpoints = []
        response = self._make_api_request("node/class/fvCEp.json")
        
        if response and 'imdata' in response:
            for item in response['imdata']:
                endpoint = item.get('fvCEp', {}).get('attributes', {})
                if endpoint:
                    endpoints.append({
                        'ip': endpoint.get('ip', 'N/A'),
                        'mac': endpoint.get('mac', 'N/A'),
                        'tenant': endpoint.get('dn', '').split('/')[1].replace('tn-', '') if 'dn' in endpoint else 'N/A',
                        'vrf': endpoint.get('lcCtx', 'N/A'),
                        'bd': endpoint.get('bdName', 'N/A'),
                        'interface': endpoint.get('ifId', 'N/A')
                    })
        
        logger.info(f"Found {len(endpoints)} endpoints")
        return endpoints
    
    def find_subnets(self) -> List[Dict]:
        """Find all subnets configured in the ACI fabric.
        
        Returns:
            List of subnet dictionaries
        """
        logger.info("Discovering all subnets...")
        
        subnets = []
        response = self._make_api_request("node/class/fvSubnet.json")
        
        if response and 'imdata' in response:
            for item in response['imdata']:
                subnet = item.get('fvSubnet', {}).get('attributes', {})
                if subnet:
                    dn = subnet.get('dn', '')
                    tenant = dn.split('/')[1].replace('tn-', '') if len(dn.split('/')) > 1 else 'N/A'
                    bd = dn.split('/')[3].replace('BD-', '') if len(dn.split('/')) > 3 else 'N/A'
                    
                    subnets.append({
                        'ip': subnet.get('ip', 'N/A'),
                        'tenant': tenant,
                        'bridge_domain': bd,
                        'scope': subnet.get('scope', 'N/A'),
                        'preferred': subnet.get('preferred', 'N/A'),
                        'virtual': subnet.get('virtual', 'N/A')
                    })
        
        logger.info(f"Found {len(subnets)} subnets")
        return subnets
    
    def find_bridge_domains(self) -> List[Dict]:
        """Find all bridge domains in the ACI fabric.
        
        Returns:
            List of bridge domain dictionaries
        """
        logger.info("Discovering all bridge domains...")
        
        bridge_domains = []
        response = self._make_api_request("node/class/fvBD.json")
        
        if response and 'imdata' in response:
            for item in response['imdata']:
                bd = item.get('fvBD', {}).get('attributes', {})
                if bd:
                    dn = bd.get('dn', '')
                    tenant = dn.split('/')[1].replace('tn-', '') if len(dn.split('/')) > 1 else 'N/A'
                    
                    bridge_domains.append({
                        'name': bd.get('name', 'N/A'),
                        'tenant': tenant,
                        'mac': bd.get('mac', 'N/A'),
                        'arp_flood': bd.get('arpFlood', 'N/A'),
                        'unicast_route': bd.get('unicastRoute', 'N/A'),
                        'unknown_unicast': bd.get('unkMacUcastAct', 'N/A')
                    })
        
        logger.info(f"Found {len(bridge_domains)} bridge domains")
        return bridge_domains
    
    def search_ip(self, search_ip: str) -> List[Dict]:
        """Search for a specific IP address in the ACI fabric.
        
        Args:
            search_ip: IP address to search for
            
        Returns:
            List of matching endpoints
        """
        logger.info(f"Searching for IP address: {search_ip}")
        
        matching_endpoints = []
        response = self._make_api_request(
            "node/class/fvCEp.json",
            params={"query-target-filter": f'eq(fvCEp.ip,"{search_ip}")'}
        )
        
        if response and 'imdata' in response:
            for item in response['imdata']:
                endpoint = item.get('fvCEp', {}).get('attributes', {})
                if endpoint:
                    matching_endpoints.append({
                        'ip': endpoint.get('ip', 'N/A'),
                        'mac': endpoint.get('mac', 'N/A'),
                        'tenant': endpoint.get('dn', '').split('/')[1].replace('tn-', '') if 'dn' in endpoint else 'N/A',
                        'vrf': endpoint.get('lcCtx', 'N/A'),
                        'bd': endpoint.get('bdName', 'N/A'),
                        'interface': endpoint.get('ifId', 'N/A'),
                        'dn': endpoint.get('dn', 'N/A')
                    })
        
        logger.info(f"Found {len(matching_endpoints)} matches for IP {search_ip}")
        return matching_endpoints
    
    def logout(self):
        """Logout from the APIC controller."""
        if self.token:
            try:
                logout_url = f"{self.apic_url}/api/aaaLogout.json"
                self.session.post(logout_url, verify=self.verify_ssl, timeout=10)
                logger.info("Successfully logged out from APIC")
            except:
                pass
            finally:
                self.token = None
                self.session.close()


def format_output(data: List[Dict], output_format: str = 'table') -> str:
    """Format output data for display.
    
    Args:
        data: List of dictionaries to format
        output_format: Output format ('table', 'json', 'csv')
        
    Returns:
        Formatted string
    """
    if output_format == 'json':
        return json.dumps(data, indent=2)
    
    elif output_format == 'csv':
        if not data:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    else:  # table format
        if not data:
            return "No data found."
        
        # Calculate column widths
        headers = list(data[0].keys())
        col_widths = {header: len(header) for header in headers}
        
        for row in data:
            for header in headers:
                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
        
        # Build table
        lines = []
        
        # Header
        header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Data rows
        for row in data:
            data_line = " | ".join(str(row.get(header, '')).ljust(col_widths[header]) for header in headers)
            lines.append(data_line)
        
        return "\n".join(lines)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Cisco ACI IP Finder - Discover IP addresses in ACI environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --apic https://apic.example.com --username admin --password secret --endpoints
  %(prog)s --apic https://apic.example.com --username admin --password secret --search-ip 10.1.1.100
  %(prog)s --apic https://apic.example.com --username admin --password secret --subnets --format json
        """
    )
    
    # Connection arguments
    parser.add_argument('--apic', required=True, help='APIC controller URL')
    parser.add_argument('--username', required=True, help='Username for APIC authentication')
    parser.add_argument('--password', required=True, help='Password for APIC authentication')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificates')
    
    # Action arguments
    parser.add_argument('--endpoints', action='store_true', help='Discover all endpoints')
    parser.add_argument('--subnets', action='store_true', help='Discover all subnets')
    parser.add_argument('--bridge-domains', action='store_true', help='Discover all bridge domains')
    parser.add_argument('--search-ip', help='Search for a specific IP address')
    
    # Output arguments
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not any([args.endpoints, args.subnets, args.bridge_domains, args.search_ip]):
        parser.error("Must specify at least one action: --endpoints, --subnets, --bridge-domains, or --search-ip")
    
    # Initialize ACI IP Finder
    finder = ACIIPFinder(args.apic, args.username, args.password, args.verify_ssl)
    
    try:
        # Authenticate
        if not finder.authenticate():
            print("Failed to authenticate with APIC. Please check your credentials.", file=sys.stderr)
            return 1
        
        # Execute requested actions
        if args.search_ip:
            results = finder.search_ip(args.search_ip)
            print(f"\nSearch results for IP: {args.search_ip}")
            print(format_output(results, args.format))
        
        if args.endpoints:
            results = finder.find_all_endpoints()
            print(f"\nAll Endpoints ({len(results)} found):")
            print(format_output(results, args.format))
        
        if args.subnets:
            results = finder.find_subnets()
            print(f"\nAll Subnets ({len(results)} found):")
            print(format_output(results, args.format))
        
        if args.bridge_domains:
            results = finder.find_bridge_domains()
            print(f"\nAll Bridge Domains ({len(results)} found):")
            print(format_output(results, args.format))
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        finder.logout()


if __name__ == '__main__':
    sys.exit(main())