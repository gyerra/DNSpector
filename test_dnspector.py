#!/usr/bin/env python3
"""
Test script for DNSpector components
"""

import sys
import time
from monitor import resolve_and_log, compare_doh_resolvers
from db import DNSDatabase

def test_basic_resolution():
    """Test basic DNS resolution"""
    print("🔍 Testing basic DNS resolution...")
    results = resolve_and_log("google.com")
    
    for resolver, data in results.items():
        status = "✅" if data['status'] == 'NOERROR' else "❌"
        print(f"  {status} {resolver}: {data['ip']} ({data['latency_ms']:.1f}ms)")
    
    return all(data['status'] == 'NOERROR' for data in results.values())

def test_doh_comparison():
    """Test DoH vs UDP comparison"""
    print("\n🔍 Testing DoH vs UDP comparison...")
    results = compare_doh_resolvers("github.com")
    
    for resolver, data in results.items():
        status = "✅" if data['status'] == 'NOERROR' else "❌"
        print(f"  {status} {resolver}: {data['ip']} ({data['latency_ms']:.1f}ms)")
    
    return all(data['status'] == 'NOERROR' for data in results.values())

def test_database():
    """Test database operations"""
    print("\n🗄️ Testing database operations...")
    db = DNSDatabase()
    
    # Test getting domains
    domains = db.get_all_domains()
    print(f"  Found {len(domains)} domains in database")
    
    # Test getting resolvers
    resolvers = db.get_all_resolvers()
    print(f"  Found {len(resolvers)} resolvers in database")
    
    # Test getting domain history
    if domains:
        history = db.get_domain_history(domains[0], limit=5)
        print(f"  Found {len(history)} history entries for {domains[0]}")
    
    return True

def test_ip_change_detection():
    """Test IP change detection"""
    print("\n🚨 Testing IP change detection...")
    db = DNSDatabase()
    
    # Simulate IP change
    domain = "test.example.com"
    resolver = "test_resolver"
    
    # First resolution
    db.log_dns_result(domain, resolver, "192.168.1.1", 300, "NOERROR", 50.0)
    
    # Second resolution with different IP
    db.log_dns_result(domain, resolver, "192.168.1.2", 300, "NOERROR", 45.0)
    
    # Check if alert was created
    alerts = db.get_recent_alerts(limit=10)
    ip_change_alerts = [a for a in alerts if a['domain'] == domain and a['reason'] == 'IP_CHANGED']
    
    if ip_change_alerts:
        print(f"  ✅ IP change alert detected: {ip_change_alerts[0]['old_ip']} → {ip_change_alerts[0]['new_ip']}")
        return True
    else:
        print("  ❌ No IP change alert detected")
        return False

def main():
    """Run all tests"""
    print("🧪 DNSpector Component Tests")
    print("=" * 40)
    
    tests = [
        ("Basic DNS Resolution", test_basic_resolution),
        ("DoH Comparison", test_doh_comparison),
        ("Database Operations", test_database),
        ("IP Change Detection", test_ip_change_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  ✅ {test_name} passed")
            else:
                print(f"  ❌ {test_name} failed")
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! DNSpector is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 