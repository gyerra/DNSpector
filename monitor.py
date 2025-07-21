import os
import csv
import logging
from datetime import datetime
from time import perf_counter
from resolver import resolve

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'dnspector_log.csv')
CSV_HEADERS = ['Domain', 'IP', 'TTL', 'Status', 'Response Time (ms)', 'Timestamp']

# Configure logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'dnspector_debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def ensure_log_file():
    """Ensure the log directory and CSV file exist, and write headers if new."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def log_dns_result(domain, ip, ttl, status, latency_ms):
    """
    Log the DNS query result to the CSV file.
    """
    ensure_log_file()
    timestamp = datetime.utcnow().isoformat()
    row = [domain, ip or '', ttl if ttl is not None else '', status, f'{latency_ms:.2f}', timestamp]
    try:
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    except Exception as e:
        logging.error(f'Failed to write log for {domain}: {e}')

def resolve_and_log(domain):
    """
    Resolve the domain, measure response time, classify errors, and log the result.
    """
    logging.info(f'Resolving domain: {domain}')
    start = perf_counter()
    try:
        ip, ttl, status, latency = resolve(domain)
        latency_ms = (perf_counter() - start) * 1000 if latency is None else latency
        # Classify errors
        if status == 'TIMEOUT':
            logging.warning(f'Timeout for {domain}')
        elif status in ('NXDOMAIN', 'SERVFAIL'):
            logging.warning(f'DNS error {status} for {domain}')
        elif ip is None:
            logging.warning(f'No response or parsing error for {domain}')
        log_dns_result(domain, ip, ttl, status, latency_ms)
        return ip, ttl, status, latency_ms
    except Exception as e:
        latency_ms = (perf_counter() - start) * 1000
        logging.error(f'Exception resolving {domain}: {e}')
        log_dns_result(domain, None, None, f'EXCEPTION: {e}', latency_ms)
        return None, None, f'EXCEPTION: {e}', latency_ms 