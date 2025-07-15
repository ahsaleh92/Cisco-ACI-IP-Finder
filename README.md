# Cisco ACI IP Finder

A Python tool for discovering and finding IP addresses in Cisco ACI (Application Centric Infrastructure) environments. This tool connects to Cisco APIC controllers to query and discover endpoints, subnets, bridge domains, and search for specific IP addresses.

## Features

- **Endpoint Discovery**: Find all endpoints (IP/MAC addresses) in the ACI fabric
- **Subnet Discovery**: Discover all configured subnets across tenants and bridge domains
- **Bridge Domain Discovery**: List all bridge domains and their configurations
- **IP Address Search**: Search for specific IP addresses and their associated details
- **Multiple Output Formats**: Support for table, JSON, and CSV output formats
- **Secure Authentication**: Support for HTTPS with optional SSL verification
- **Comprehensive Logging**: Detailed logging for troubleshooting and auditing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ahsaleh92/Cisco-ACI-IP-Finder.git
cd Cisco-ACI-IP-Finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x aci_ip_finder.py
```

## Usage

### Basic Usage

The tool requires connection to a Cisco APIC controller. You must provide the APIC URL, username, and password.

### Command Line Options

```
usage: aci_ip_finder.py [-h] --apic APIC --username USERNAME --password PASSWORD
                        [--verify-ssl] [--endpoints] [--subnets] [--bridge-domains]
                        [--search-ip SEARCH_IP] [--format {table,json,csv}] [--verbose]

Connection Options:
  --apic APIC           APIC controller URL (e.g., https://apic.example.com)
  --username USERNAME   Username for APIC authentication
  --password PASSWORD   Password for APIC authentication
  --verify-ssl          Verify SSL certificates (default: disabled)

Discovery Options:
  --endpoints           Discover all endpoints (IP/MAC addresses)
  --subnets             Discover all subnets
  --bridge-domains      Discover all bridge domains
  --search-ip IP        Search for a specific IP address

Output Options:
  --format FORMAT       Output format: table, json, csv (default: table)
  --verbose, -v         Enable verbose logging
```

### Examples

#### 1. Find All Endpoints
```bash
python aci_ip_finder.py --apic https://apic.example.com --username admin --password secret --endpoints
```

#### 2. Search for a Specific IP Address
```bash
python aci_ip_finder.py --apic https://apic.example.com --username admin --password secret --search-ip 10.1.1.100
```

#### 3. Discover All Subnets with JSON Output
```bash
python aci_ip_finder.py --apic https://apic.example.com --username admin --password secret --subnets --format json
```

#### 4. Find All Bridge Domains with CSV Output
```bash
python aci_ip_finder.py --apic https://apic.example.com --username admin --password secret --bridge-domains --format csv > bridge_domains.csv
```

#### 5. Multiple Actions with Verbose Logging
```bash
python aci_ip_finder.py --apic https://apic.example.com --username admin --password secret --endpoints --subnets --verbose
```

## Output Formats

### Table Format (Default)
Human-readable table format suitable for terminal viewing:
```
ip          | mac               | tenant | vrf     | bd        | interface
10.1.1.100  | 00:50:56:12:34:56 | prod   | prod-vrf| web-bd    | eth1/1
10.1.1.101  | 00:50:56:12:34:57 | prod   | prod-vrf| web-bd    | eth1/2
```

### JSON Format
Structured JSON output suitable for programmatic processing:
```json
[
  {
    "ip": "10.1.1.100",
    "mac": "00:50:56:12:34:56",
    "tenant": "prod",
    "vrf": "prod-vrf",
    "bd": "web-bd",
    "interface": "eth1/1"
  }
]
```

### CSV Format
Comma-separated values suitable for spreadsheet import:
```csv
ip,mac,tenant,vrf,bd,interface
10.1.1.100,00:50:56:12:34:56,prod,prod-vrf,web-bd,eth1/1
10.1.1.101,00:50:56:12:34:57,prod,prod-vrf,web-bd,eth1/2
```

## Security Considerations

- **SSL Verification**: By default, SSL certificate verification is disabled for convenience with self-signed certificates. Use `--verify-ssl` for production environments with valid certificates.
- **Credentials**: Never hardcode credentials in scripts. Consider using environment variables or secure credential storage.
- **Network Access**: Ensure the tool is run from a network location that can reach the APIC management interface.

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify APIC URL is correct and accessible
   - Check username/password credentials
   - Ensure account has read permissions for fabric discovery

2. **SSL Certificate Errors**
   - Use `--verify-ssl` flag only with valid certificates
   - For self-signed certificates, omit the `--verify-ssl` flag

3. **Connection Timeouts**
   - Check network connectivity to APIC
   - Verify firewall rules allow HTTPS traffic
   - Ensure APIC is not overloaded

4. **No Data Returned**
   - Verify user has appropriate read permissions
   - Check if there are actually endpoints/subnets configured
   - Use `--verbose` flag for detailed logging

### Enable Debug Logging

For detailed troubleshooting, use verbose mode:
```bash
python aci_ip_finder.py --verbose --apic https://apic.example.com --username admin --password secret --endpoints
```

## API Reference

The tool queries the following APIC REST API endpoints:

- **Endpoints**: `/api/node/class/fvCEp.json`
- **Subnets**: `/api/node/class/fvSubnet.json`
- **Bridge Domains**: `/api/node/class/fvBD.json`
- **Authentication**: `/api/aaaLogin.json`
- **Logout**: `/api/aaaLogout.json`

## Requirements

- Python 3.6 or later
- Network access to Cisco APIC controller
- Valid APIC user account with read permissions

## Dependencies

- `requests`: HTTP library for API communication
- `urllib3`: HTTP client library (for SSL handling)

## License

This project is open source. Please refer to the license file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Enable verbose logging to gather more information
3. Submit an issue with detailed information about your environment and the problem