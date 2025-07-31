import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DNSDatabase:
    """SQLite database for storing DNS monitoring data"""
    
    def __init__(self, db_path: str = 'dns_log.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create DNS resolution logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dns_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    resolver TEXT NOT NULL,
                    ip TEXT,
                    ttl INTEGER,
                    status TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create IP change alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    resolver TEXT NOT NULL,
                    old_ip TEXT,
                    new_ip TEXT,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON dns_logs(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resolver ON dns_logs(resolver)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON dns_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain_resolver ON dns_logs(domain, resolver)')
            
            conn.commit()
    
    def log_dns_result(self, domain: str, resolver: str, ip: Optional[str], 
                      ttl: Optional[int], status: str, latency_ms: float):
        """Log a DNS resolution result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dns_logs (domain, resolver, ip, ttl, status, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain, resolver, ip, ttl, status, latency_ms))
            conn.commit()
        
        # Check for IP changes after logging
        if ip and status == 'NOERROR':
            self._check_ip_change(domain, resolver, ip)
    
    def _check_ip_change(self, domain: str, resolver: str, new_ip: str):
        """Internal method to check for IP changes and log alerts"""
        last_ip = self.get_last_ip(domain, resolver)
        if last_ip and last_ip != new_ip:
            self.log_ip_alert(domain, resolver, last_ip, new_ip, 'IP_CHANGED')
    
    def log_ip_alert(self, domain: str, resolver: str, old_ip: Optional[str], 
                    new_ip: Optional[str], reason: str):
        """Log an IP change alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ip_alerts (domain, resolver, old_ip, new_ip, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (domain, resolver, old_ip, new_ip, reason))
            conn.commit()
    
    def get_last_ip(self, domain: str, resolver: str) -> Optional[str]:
        """Get the last known IP for a domain/resolver combination"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ip FROM dns_logs 
                WHERE domain = ? AND resolver = ? AND ip IS NOT NULL
                ORDER BY timestamp DESC LIMIT 1
            ''', (domain, resolver))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_domain_history(self, domain: str, resolver: Optional[str] = None, 
                          limit: int = 100) -> List[Dict]:
        """Get DNS resolution history for a domain"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if resolver:
                cursor.execute('''
                    SELECT * FROM dns_logs 
                    WHERE domain = ? AND resolver = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (domain, resolver, limit))
            else:
                cursor.execute('''
                    SELECT * FROM dns_logs 
                    WHERE domain = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (domain, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_domains(self) -> List[str]:
        """Get list of all monitored domains"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT domain FROM dns_logs ORDER BY domain')
            return [row[0] for row in cursor.fetchall()]
    
    def get_all_resolvers(self) -> List[str]:
        """Get list of all used resolvers"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT resolver FROM dns_logs ORDER BY resolver')
            return [row[0] for row in cursor.fetchall()]
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent IP change alerts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ip_alerts 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def export_to_csv(self, filename: str, domain: Optional[str] = None, 
                     resolver: Optional[str] = None):
        """Export DNS logs to CSV file"""
        import csv
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if domain and resolver:
                cursor.execute('''
                    SELECT domain, resolver, ip, ttl, status, latency_ms, timestamp
                    FROM dns_logs 
                    WHERE domain = ? AND resolver = ?
                    ORDER BY timestamp DESC
                ''', (domain, resolver))
            elif domain:
                cursor.execute('''
                    SELECT domain, resolver, ip, ttl, status, latency_ms, timestamp
                    FROM dns_logs 
                    WHERE domain = ?
                    ORDER BY timestamp DESC
                ''', (domain,))
            else:
                cursor.execute('''
                    SELECT domain, resolver, ip, ttl, status, latency_ms, timestamp
                    FROM dns_logs 
                    ORDER BY timestamp DESC
                ''')
            
            rows = cursor.fetchall()
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Domain', 'Resolver', 'IP', 'TTL', 'Status', 'Latency (ms)', 'Timestamp'])
                writer.writerows(rows)
    
    def export_to_json(self, filename: str, domain: Optional[str] = None, 
                      resolver: Optional[str] = None):
        """Export DNS logs to JSON file"""
        data = self.get_domain_history(domain or '', resolver, limit=10000)
        
        with open(filename, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str) 