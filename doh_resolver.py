import base64
import json
import time
from typing import Tuple, Optional
import urllib.request
import urllib.parse

class DoHResolver:
    """DNS-over-HTTPS resolver using Google's and Cloudflare's DoH APIs"""
    
    def __init__(self):
        self.google_doh = "https://dns.google/resolve"
        self.cloudflare_doh = "https://cloudflare-dns.com/dns-query"
        
    def _build_doh_query(self, domain: str) -> str:
        """Build a DNS query in base64url format for DoH"""
        # Simple DNS query structure for A record
        # This is a simplified version - in production you'd want a proper DNS packet builder
        query = f"?name={domain}&type=A"
        return query
    
    def _parse_doh_response(self, response_data: dict) -> Tuple[Optional[str], Optional[int], str]:
        """Parse DoH JSON response and extract IP, TTL, and status"""
        try:
            if response_data.get('Status') != 0:
                return None, None, f'DOH_ERROR_{response_data.get("Status")}'
            
            answers = response_data.get('Answer', [])
            for answer in answers:
                if answer.get('type') == 1:  # A record
                    ip = answer.get('data')
                    ttl = answer.get('TTL')
                    return ip, ttl, 'NOERROR'
            
            return None, None, 'NO_ANSWER'
        except Exception as e:
            return None, None, f'PARSE_ERROR: {e}'
    
    def resolve_google(self, domain: str, timeout: float = 5.0) -> Tuple[Optional[str], Optional[int], str, float]:
        """Resolve domain using Google's DoH API"""
        start_time = time.time()
        try:
            query = self._build_doh_query(domain)
            url = f"{self.google_doh}{query}"
            
            req = urllib.request.Request(url)
            req.add_header('Accept', 'application/dns-json')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode())
            
            response_time = (time.time() - start_time) * 1000
            ip, ttl, status = self._parse_doh_response(data)
            return ip, ttl, status, response_time
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return None, None, f'DOH_ERROR: {e}', response_time
    
    def resolve_cloudflare(self, domain: str, timeout: float = 5.0) -> Tuple[Optional[str], Optional[int], str, float]:
        """Resolve domain using Cloudflare's DoH API"""
        start_time = time.time()
        try:
            query = self._build_doh_query(domain)
            url = f"{self.cloudflare_doh}{query}"
            
            req = urllib.request.Request(url)
            req.add_header('Accept', 'application/dns-json')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode())
            
            response_time = (time.time() - start_time) * 1000
            ip, ttl, status = self._parse_doh_response(data)
            return ip, ttl, status, response_time
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return None, None, f'DOH_ERROR: {e}', response_time 