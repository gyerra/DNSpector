import argparse
import sys
from monitor import resolve_and_log

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

def main():
    parser = argparse.ArgumentParser(
        description='DNSpector: DNS inspection and monitoring tool (custom dig/nslookup)'
    )
    parser.add_argument('-d', '--domain', type=str, help='Domain name to query')
    parser.add_argument('-f', '--file', type=str, help='File with domain names (one per line)')
    parser.add_argument('-r', '--record', type=str, default='A', help='DNS record type (default: A)')
    parser.add_argument('--verbose', action='store_true', help='Print parsed output to stdout')
    parser.add_argument('--compare', action='store_true', help='Compare multiple DNS providers (to be implemented)')
    args = parser.parse_args()

    if args.record.upper() != 'A':
        print('Only A record queries are supported in this version.')
        sys.exit(1)

    if not args.domain and not args.file:
        parser.print_help()
        sys.exit(1)

    if args.domain:
        ip, ttl, status, latency = resolve_and_log(args.domain)
        if args.verbose:
            print(f'Domain: {args.domain}\n  IP: {ip}\n  TTL: {ttl}\n  Status: {status}\n  Response Time: {latency:.2f} ms')

    if args.file:
        try:
            with open(args.file, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f'Error reading file {args.file}: {e}')
            sys.exit(1)
        iterator = tqdm(domains, desc='Querying', unit='domain') if tqdm else domains
        for domain in iterator:
            ip, ttl, status, latency = resolve_and_log(domain)
            if args.verbose:
                print(f'Domain: {domain}\n  IP: {ip}\n  TTL: {ttl}\n  Status: {status}\n  Response Time: {latency:.2f} ms')

if __name__ == '__main__':
    main() 