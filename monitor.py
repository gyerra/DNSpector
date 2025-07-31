import os
import csv
import logging
import socket
from datetime import datetime
from time import perf_counter
from resolver import resolve
from doh_resolver import DoHResolver
from db import DNSDatabase

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'dnspector_log.csv')
CSV_HEADERS = ['Domain', 'Resolver', 'IP', 'TTL', 'Status', 'Response Time (ms)', 'Timestamp']

# Ensure logs directory exists before configuring logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'dnspector_debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Initialize database and resolvers
db = DNSDatabase()
doh_resolver = DoHResolver()

# DNS resolvers configuration
RESOLVERS = {
    'google': '8.8.8.8',
    'cloudflare': '1.1.1.1',
    'system': None  # Will use system default
}

def ensure_log_file():
    """Ensure the log directory and CSV file exist, and write headers if new."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def resolve_system(domain: str, timeout: float = 2.0):
    """Resolve domain using system default DNS resolver"""
    start = perf_counter()
    try:
        ip = socket.gethostbyname(domain)
        latency_ms = (perf_counter() - start) * 1000
        return ip, None, 'NOERROR', latency_ms
    except socket.gaierror as e:
        latency_ms = (perf_counter() - start) * 1000
        return None, None, f'GAIERRO: {e}', latency_ms
    except Exception as e:
        latency_ms = (perf_counter() - start) * 1000
        return None, None, f'EXCEPTION: {e}', latency_ms

def resolve_with_resolver(domain: str, resolver_name: str):
    """Resolve domain using specified resolver"""
    logging.info(f'Resolving {domain} with {resolver_name}')
    
    if resolver_name == 'google':
        ip, ttl, status, latency_ms = resolve(domain, RESOLVERS['google'])
    elif resolver_name == 'cloudflare':
        ip, ttl, status, latency_ms = resolve(domain, RESOLVERS['cloudflare'])
    elif resolver_name == 'system':
        ip, ttl, status, latency_ms = resolve_system(domain)
    elif resolver_name == 'google_doh':
        ip, ttl, status, latency_ms = doh_resolver.resolve_google(domain)
    elif resolver_name == 'cloudflare_doh':
        ip, ttl, status, latency_ms = doh_resolver.resolve_cloudflare(domain)
    else:
        logging.error(f'Unknown resolver: {resolver_name}')
        return None, None, 'UNKNOWN_RESOLVER', 0.0
    
    # Log to database (IP change detection is handled automatically)
    db.log_dns_result(domain, resolver_name, ip, ttl, status, latency_ms)
    
    return ip, ttl, status, latency_ms

def resolve_and_log(domain):
    """
    Resolve the domain with all resolvers, measure response time, and log results.
    """
    results = {}
    
    for resolver_name in ['google', 'cloudflare', 'system']:
        try:
            ip, ttl, status, latency_ms = resolve_with_resolver(domain, resolver_name)
            results[resolver_name] = {
                'ip': ip,
                'ttl': ttl,
                'status': status,
                'latency_ms': latency_ms
            }
            
            # Log warnings for errors
            if status == 'TIMEOUT':
                logging.warning(f'Timeout for {domain} with {resolver_name}')
            elif status in ('NXDOMAIN', 'SERVFAIL'):
                logging.warning(f'DNS error {status} for {domain} with {resolver_name}')
            elif ip is None:
                logging.warning(f'No response for {domain} with {resolver_name}')
                
        except Exception as e:
            logging.error(f'Exception resolving {domain} with {resolver_name}: {e}')
            results[resolver_name] = {
                'ip': None,
                'ttl': None,
                'status': f'EXCEPTION: {e}',
                'latency_ms': 0.0
            }
    
    return results

def monitor_domains(domains: list, interval: int = 600):
    """
    Monitor a list of domains at specified intervals.
    """
    import time
    
    logging.info(f'Starting monitoring of {len(domains)} domains every {interval} seconds')
    
    while True:
        for domain in domains:
            try:
                results = resolve_and_log(domain)
                logging.info(f'Monitored {domain}: {results}')
            except Exception as e:
                logging.error(f'Error monitoring {domain}: {e}')
        
        logging.info(f'Sleeping for {interval} seconds...')
        time.sleep(interval)

def compare_doh_resolvers(domain: str):
    """
    Compare UDP vs DoH resolvers for a domain.
    """
    results = {}
    
    # UDP resolvers
    for resolver_name in ['google', 'cloudflare']:
        ip, ttl, status, latency_ms = resolve_with_resolver(domain, resolver_name)
        results[f'{resolver_name}_udp'] = {
            'ip': ip,
            'ttl': ttl,
            'status': status,
            'latency_ms': latency_ms
        }
    
    # DoH resolvers
    for resolver_name in ['google_doh', 'cloudflare_doh']:
        ip, ttl, status, latency_ms = resolve_with_resolver(domain, resolver_name)
        results[resolver_name] = {
            'ip': ip,
            'ttl': ttl,
            'status': status,
            'latency_ms': latency_ms
        }
    
    return results 