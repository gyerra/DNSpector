import argparse
import sys
import time
from monitor import resolve_and_log, monitor_domains, compare_doh_resolvers
from dashboard import app

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

def main():
    parser = argparse.ArgumentParser(
        description='DNSpector: Comprehensive DNS monitoring and debugging tool'
    )
    
    # Basic query options
    parser.add_argument('-d', '--domain', type=str, help='Domain name to query')
    parser.add_argument('-f', '--file', type=str, help='File with domain names (one per line)')
    parser.add_argument('--verbose', action='store_true', help='Print detailed output to stdout')
    
    # Monitoring options
    parser.add_argument('--monitor', type=str, help='Start monitoring domains from file')
    parser.add_argument('--interval', type=int, default=600, help='Monitoring interval in seconds (default: 600)')
    
    # Comparison options
    parser.add_argument('--compare', action='store_true', help='Compare all DNS resolvers')
    parser.add_argument('--doh-benchmark', action='store_true', help='Compare UDP vs DoH resolvers')
    
    # Dashboard options
    parser.add_argument('--dashboard', action='store_true', help='Launch web dashboard')
    parser.add_argument('--port', type=int, default=5000, help='Dashboard port (default: 5000)')
    
    args = parser.parse_args()

    if not any([args.domain, args.file, args.monitor, args.dashboard]):
        parser.print_help()
        sys.exit(1)

    # Launch dashboard
    if args.dashboard:
        print(f"🚀 Starting DNSpector Dashboard on http://localhost:{args.port}")
        print("Press Ctrl+C to stop the dashboard")
        try:
            app.run(debug=False, host='0.0.0.0', port=args.port)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")
        return

    # Start monitoring
    if args.monitor:
        try:
            with open(args.monitor, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            print(f"🔍 Starting monitoring of {len(domains)} domains every {args.interval} seconds")
            print("Press Ctrl+C to stop monitoring")
            monitor_domains(domains, args.interval)
        except FileNotFoundError:
            print(f"❌ Error: File {args.monitor} not found")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
        return

    # Single domain query with comparison
    if args.domain:
        if args.compare:
            print(f"🔍 Comparing resolvers for {args.domain}:")
            results = resolve_and_log(args.domain)
            for resolver, data in results.items():
                print(f"\n{resolver.upper()}:")
                print(f"  IP: {data['ip']}")
                print(f"  TTL: {data['ttl']}")
                print(f"  Status: {data['status']}")
                print(f"  Latency: {data['latency_ms']:.2f} ms")
        elif args.doh_benchmark:
            print(f"🔍 Benchmarking DoH vs UDP for {args.domain}:")
            results = compare_doh_resolvers(args.domain)
            for resolver, data in results.items():
                print(f"\n{resolver.upper()}:")
                print(f"  IP: {data['ip']}")
                print(f"  TTL: {data['ttl']}")
                print(f"  Status: {data['status']}")
                print(f"  Latency: {data['latency_ms']:.2f} ms")
        else:
            results = resolve_and_log(args.domain)
            if args.verbose:
                for resolver, data in results.items():
                    print(f"\n{resolver.upper()}:")
                    print(f"  IP: {data['ip']}")
                    print(f"  TTL: {data['ttl']}")
                    print(f"  Status: {data['status']}")
                    print(f"  Latency: {data['latency_ms']:.2f} ms")
            else:
                # Show summary
                print(f"Domain: {args.domain}")
                for resolver, data in results.items():
                    status_icon = "✅" if data['status'] == 'NOERROR' else "❌"
                    print(f"  {status_icon} {resolver}: {data['ip']} ({data['latency_ms']:.1f}ms)")

    # Multiple domains from file
    if args.file:
        try:
            with open(args.file, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f'❌ Error reading file {args.file}: {e}')
            sys.exit(1)
        
        if args.compare:
            print(f"🔍 Comparing resolvers for {len(domains)} domains:")
            iterator = tqdm(domains, desc='Querying', unit='domain') if tqdm else domains
            for domain in iterator:
                results = resolve_and_log(domain)
                if args.verbose:
                    print(f"\n{domain}:")
                    for resolver, data in results.items():
                        print(f"  {resolver}: {data['ip']} ({data['latency_ms']:.1f}ms)")
        else:
            iterator = tqdm(domains, desc='Querying', unit='domain') if tqdm else domains
            for domain in iterator:
                results = resolve_and_log(domain)
                if args.verbose:
                    print(f"\n{domain}:")
                    for resolver, data in results.items():
                        status_icon = "✅" if data['status'] == 'NOERROR' else "❌"
                        print(f"  {status_icon} {resolver}: {data['ip']} ({data['latency_ms']:.1f}ms)")

if __name__ == '__main__':
    main() 