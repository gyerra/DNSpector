# DNSpector

**DNS Monitoring and Analysis Tool**

A Python-based DNS monitoring tool that provides comprehensive DNS resolution analysis, multi-resolver comparison, and basic anomaly detection. Built with custom DNS protocol implementation and designed for network administrators, security professionals, and developers who need detailed DNS visibility.

## Overview

DNSpector implements DNS protocol from scratch using RFC 1035 standards, providing multi-resolver comparison, DNS-over-HTTPS (DoH) support, and basic IP change detection. Features include custom UDP DNS resolver, DoH client implementation, SQLite-based data storage, and web dashboard for visualization.

## Key Features

### Core DNS Resolution
- **Custom DNS Implementation**: Built from scratch using RFC 1035 standards with raw socket programming
- **Multi-Resolver Support**: Simultaneous queries to Google (8.8.8.8), Cloudflare (1.1.1.1), and system default resolvers
- **DNS-over-HTTPS (DoH)**: Support for Google's and Cloudflare's DoH APIs with performance comparison
- **Protocol Control**: Complete control over DNS packet structure and parsing

### Monitoring & Analysis
- **IP Change Detection**: Basic threshold-based detection of domain IP address changes
- **Performance Tracking**: Response time and TTL monitoring across multiple resolvers
- **Historical Data**: SQLite-based storage with timestamp tracking for trend analysis
- **Multi-Resolver Comparison**: Compare results across different DNS providers

### Data Management
- **SQLite Database**: Lightweight storage with proper indexing for DNS resolution history
- **Export Functionality**: CSV and JSON export capabilities for data analysis
- **Web Dashboard**: Flask-based interface with Chart.js for data visualization
- **CLI Interface**: Command-line tools for automation and scripting

### Basic Security Features
- **Anomaly Detection**: Simple IP change alerting with configurable thresholds
- **Response Time Monitoring**: Track DNS resolution performance and identify issues
- **Multi-Source Validation**: Compare results across different DNS resolvers

## Installation

### Requirements
- **Python**: 3.7 or higher
- **Memory**: 512MB minimum
- **Storage**: 1GB+ for database and logs
- **Network**: Outbound UDP/53 and HTTPS/443 access for DNS queries

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd DNSpector

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_dnspector.py

# Test basic functionality
python cli.py --domain google.com --verbose
```

## Usage

### Basic Operations

**Single Domain Query**
```bash
# Basic resolution with all resolvers
python cli.py --domain google.com

# Detailed analysis with verbose output
python cli.py --domain google.com --verbose

# Compare all resolvers
python cli.py --domain google.com --compare
```

**Batch Processing**
```bash
# Process domain list
python cli.py --file domains.txt

# Monitor domains at intervals
python cli.py --monitor domains.txt --interval 600
```

### Advanced Features

**DNS-over-HTTPS Benchmarking**
```bash
# Compare UDP vs DoH performance
python cli.py --domain google.com --doh-benchmark
```

**Web Dashboard**
```bash
# Launch dashboard
python cli.py --dashboard --port 5000

# Access via: http://localhost:5000
```

## Project Structure

### Component Architecture
```
DNSpector/
├── cli.py                 # Command-line interface
├── resolver.py            # Custom DNS resolver implementation
├── doh_resolver.py        # DNS-over-HTTPS client
├── monitor.py             # Monitoring and anomaly detection
├── db.py                  # SQLite database operations
├── dashboard.py           # Flask web application
├── templates/
│   └── dashboard.html     # Dashboard HTML template
├── test_dnspector.py      # Test suite
├── requirements.txt       # Python dependencies
├── domains.txt            # Sample domain list
├── dns_log.db             # SQLite database
└── logs/                  # Application logs
```

### Data Flow Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DNS Resolvers │    │  DoH Endpoints  │    │  System Resolver│
│   (UDP/53)      │    │   (HTTPS/443)   │    │   (OS Default)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    DNSpector Core         │
                    │  ┌─────────────────────┐  │
                    │  │   Packet Crafting   │  │
                    │  │   & Parsing Engine  │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Anomaly Detection  │  │
                    │  │     Engine          │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   SQLite Database        │
                    │     (Time-Series Data)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Web Dashboard          │
                    │  ┌─────────────────────┐  │
                    │  │   RESTful API       │  │
                    │  │   Data Visualization│  │
                    │  │   Export Functions  │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

## API Reference

### Dashboard Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard interface |
| `/api/data/<domain>` | GET | DNS history data for visualization |
| `/api/alerts` | GET | Recent IP change alerts |
| `/api/domains` | GET | List of all monitored domains |
| `/api/resolvers` | GET | List of available resolvers |
| `/export/csv` | GET | Export DNS data as CSV |
| `/export/json` | GET | Export DNS data as JSON |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolver` | string | all | Filter by specific DNS resolver |
| `limit` | integer | 100 | Number of data points |
| `domain` | string | required | Target domain for exports |

## Database Schema

### dns_logs Table
Stores DNS resolution results with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| domain | TEXT | Domain name being resolved |
| resolver | TEXT | DNS resolver used (google, cloudflare, system, etc.) |
| ip | TEXT | Resolved IP address |
| ttl | INTEGER | Time to live value |
| status | TEXT | DNS response status (NOERROR, NXDOMAIN, etc.) |
| latency_ms | REAL | Response time in milliseconds |
| timestamp | DATETIME | Query timestamp |

### ip_alerts Table
Tracks IP address changes for anomaly detection:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| domain | TEXT | Domain name |
| resolver | TEXT | DNS resolver used |
| old_ip | TEXT | Previous IP address |
| new_ip | TEXT | New IP address |
| reason | TEXT | Alert reason (IP_CHANGED, etc.) |
| timestamp | DATETIME | Alert timestamp |

### Database Indexes
```sql
-- Performance indexes
CREATE INDEX idx_domain ON dns_logs(domain);
CREATE INDEX idx_resolver ON dns_logs(resolver);
CREATE INDEX idx_timestamp ON dns_logs(timestamp);
CREATE INDEX idx_domain_resolver ON dns_logs(domain, resolver);
```

## Configuration

### Monitoring Intervals
- **Default**: 600 seconds (10 minutes)
- **Minimum**: 10 seconds
- **Recommended**: 300-1800 seconds for monitoring

### Supported Resolvers
- **google**: Google DNS (8.8.8.8)
- **cloudflare**: Cloudflare DNS (1.1.1.1)
- **system**: System default resolver
- **google_doh**: Google DNS-over-HTTPS
- **cloudflare_doh**: Cloudflare DNS-over-HTTPS

### Logging
- **Application logs**: `logs/dnspector_debug.log`
- **CSV exports**: `logs/dns_export_*.csv`
- **JSON exports**: `logs/dns_export_*.json`

### Network Requirements
- **UDP/53**: Standard DNS resolution
- **HTTPS/443**: DNS-over-HTTPS queries

## Testing

### Test Suite
```bash
# Run complete test suite
python test_dnspector.py
```

**Test Coverage**
- Basic DNS resolution functionality
- DoH resolver performance
- Database operations and schema
- IP change detection algorithms

### Performance Testing
```bash
# Test resolver comparison
python cli.py --domain google.com --compare

# Test DoH benchmarking
python cli.py --domain google.com --doh-benchmark
```

**Expected Performance**
- **UDP Resolution**: 15-50ms average response time
- **DoH Resolution**: 100-300ms average response time

## Performance

### DNS Resolution Performance
- **UDP Protocol**: 15-50ms average response time
- **DoH Protocol**: 100-300ms average response time
- **Multi-Resolver**: Simultaneous queries to multiple DNS servers

### Database Performance
- **SQLite Storage**: Lightweight database with proper indexing
- **Memory Usage**: Minimal memory footprint
- **Data Retention**: Configurable based on storage requirements

### Resource Requirements
- **Small Scale**: 512MB RAM, 1GB storage
- **Medium Scale**: 1GB RAM, 5GB storage
- **Large Scale**: 2GB RAM, 20GB storage

## Troubleshooting

### Common Issues

**Permission Errors**
- Ensure write permissions for logs/ and database directories
- Run with appropriate user privileges

**Network Connectivity**
- Verify internet connectivity for external resolvers
- Check firewall settings for UDP port 53 and HTTPS

**Dashboard Access**
- Confirm port availability (default: 5000)
- Check firewall rules for web interface access

### Log Analysis
Review `logs/dnspector_debug.log` for detailed error information and resolution status.

## Contributing

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_dnspector.py

# Start development server
python cli.py --dashboard --port 5000
```

## What I Learned

### DNS Protocol Deep Dive
- **RFC 1035 Implementation**: Built DNS packet structure from scratch, understanding header fields, query/response formats, and response codes
- **Protocol Differences**: Learned the trade-offs between UDP DNS (fast, simple) vs DNS-over-HTTPS (privacy, firewall bypass)
- **Real-world DNS Behavior**: Experienced how actual DNS servers respond, TTL values, and common error scenarios

### Network Programming Skills
- **Raw Socket Programming**: Implemented low-level network communication without external DNS libraries
- **Packet Crafting & Parsing**: Built binary packet structures and parsed complex network responses
- **Error Handling**: Developed robust error handling for network timeouts, malformed responses, and connectivity issues

### Data Engineering & Analytics
- **Time-Series Data Design**: Designed database schema optimized for historical DNS monitoring data
- **Performance Optimization**: Implemented proper indexing strategies for fast query performance
- **Data Visualization**: Created interactive charts and dashboards for monitoring data

### Full-Stack Development
- **Backend Development**: Built RESTful APIs with Flask for data access and export functionality
- **Frontend Development**: Created responsive web dashboard with Chart.js for real-time data visualization
- **Database Integration**: Implemented SQLite with proper connection management and data persistence

### Security & Monitoring Concepts
- **Anomaly Detection**: Implemented basic IP change detection algorithms for security monitoring
- **Multi-Source Validation**: Learned to compare data from multiple sources for reliability and security
- **Monitoring Best Practices**: Designed systems for continuous monitoring with configurable intervals

### DevOps & Automation
- **CLI Development**: Built comprehensive command-line interface with argument parsing and automation capabilities
- **Testing Strategies**: Implemented comprehensive test suite covering all major components
- **Deployment Considerations**: Designed for containerization and production deployment

## Future Enhancements

### Protocol Support
- **IPv6 Support**: Add AAAA record resolution and IPv6 address handling
- **Additional Record Types**: Support for MX, CNAME, TXT, NS, and other DNS record types
- **DNS-over-TLS (DoT)**: Implement DNS-over-TLS protocol support
- **DNSSEC Validation**: Add DNSSEC signature validation and trust chain verification

### Advanced Security Features
- **Machine Learning Anomaly Detection**: Implement ML-based detection for sophisticated threat identification
- **DNS Poisoning Detection**: Enhanced algorithms to detect DNS cache poisoning attacks
- **Threat Intelligence Integration**: Connect with external threat feeds for domain reputation checking
- **Geolocation Analysis**: Track DNS resolution from different geographic locations

### Performance & Scalability
- **Asynchronous Processing**: Implement async/await for high-throughput concurrent DNS queries
- **Distributed Monitoring**: Support for multiple monitoring nodes with centralized data collection
- **Database Optimization**: Implement data compression, partitioning, and advanced indexing
- **Caching Layer**: Add Redis-based caching for frequently accessed DNS data

### Monitoring & Alerting
- **Advanced Alerting**: Email, Slack, and webhook notifications for critical events
- **Custom Thresholds**: Configurable alert thresholds per domain and resolver
- **SLA Monitoring**: Track DNS resolution performance against service level agreements
- **Trend Analysis**: Advanced statistical analysis and predictive modeling

### Integration & Automation
- **Prometheus Integration**: Native Prometheus metrics export for monitoring stack integration
- **Grafana Dashboards**: Pre-built Grafana dashboard templates
- **CI/CD Integration**: Automated DNS health checks in deployment pipelines
- **API Enhancements**: GraphQL API, real-time WebSocket connections, and bulk operations

### User Experience
- **Web UI Improvements**: Enhanced dashboard with real-time updates, filtering, and search
- **Mobile Application**: Native mobile app for DNS monitoring on-the-go
- **Configuration Management**: Web-based configuration interface
- **User Management**: Multi-user support with role-based access control

### Enterprise Features
- **Authentication & Authorization**: LDAP/AD integration and role-based permissions
- **Audit Logging**: Comprehensive audit trails for compliance requirements
- **Data Retention Policies**: Automated data archival and cleanup
- **High Availability**: Clustering and failover capabilities

### Advanced Analytics
- **Network Topology Mapping**: Visualize DNS resolution paths and dependencies
- **Performance Benchmarking**: Comprehensive DNS performance comparison tools
- **Capacity Planning**: Predictive analytics for DNS infrastructure scaling
- **Cost Optimization**: Analyze DNS resolution costs across different providers


