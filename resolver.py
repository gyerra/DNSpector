import socket
import struct
import random
import time
from typing import Tuple, Optional

# DNS query types
A_RECORD = 1
IN_CLASS = 1

# DNS response codes
RCODE = {
    0: 'NOERROR',
    1: 'FORMERR',
    2: 'SERVFAIL',
    3: 'NXDOMAIN',
    4: 'NOTIMP',
    5: 'REFUSED',
}

def build_dns_query(domain: str) -> bytes:
    """
    Construct a raw DNS query packet for the given domain (A record).
    """
    # Generate a random 16-bit identifier for the DNS query
    transaction_id = random.randint(0, 0xFFFF)
    # Flags: standard query, recursion desired
    flags = 0x0100
    qdcount = 1  # Number of questions
    ancount = nscount = arcount = 0
    # DNS header: 12 bytes
    header = struct.pack('!HHHHHH', transaction_id, flags, qdcount, ancount, nscount, arcount)

    # Encode the domain name into DNS label format
    def encode_domain(name):
        parts = name.split('.')
        return b''.join(struct.pack('B', len(part)) + part.encode() for part in parts) + b'\x00'

    qname = encode_domain(domain)
    qtype = struct.pack('!H', A_RECORD)
    qclass = struct.pack('!H', IN_CLASS)
    question = qname + qtype + qclass
    return header + question

def parse_dns_response(data: bytes) -> Tuple[Optional[str], Optional[int], str]:
    """
    Parse the DNS response and extract the first A record IP, its TTL, and the response code.
    Returns (ip, ttl, status)
    """
    # Unpack header
    if len(data) < 12:
        return None, None, 'INVALID_RESPONSE'
    (tid, flags, qdcount, ancount, nscount, arcount) = struct.unpack('!HHHHHH', data[:12])
    rcode = flags & 0x000F
    status = RCODE.get(rcode, f'RCODE_{rcode}')
    offset = 12

    # Skip question section
    for _ in range(qdcount):
        while data[offset] != 0:
            offset += 1 + data[offset]
        offset += 1  # null byte
        offset += 4  # type and class

    # Parse answer section
    ip = None
    ttl = None
    for _ in range(ancount):
        # Handle name (could be pointer)
        if data[offset] & 0xC0 == 0xC0:
            offset += 2
        else:
            while data[offset] != 0:
                offset += 1 + data[offset]
            offset += 1
        atype, aclass, attl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        if atype == A_RECORD and aclass == IN_CLASS and rdlength == 4:
            ip = '.'.join(str(b) for b in rdata)
            ttl = attl
            break  # Only first A record
    return ip, ttl, status

def resolve(domain: str, dns_server: str = '8.8.8.8', timeout: float = 2.0) -> Tuple[Optional[str], Optional[int], str, float]:
    """
    Send a DNS query for the given domain to the specified DNS server.
    Returns (ip, ttl, status, response_time_ms)
    """
    query = build_dns_query(domain)
    start = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(query, (dns_server, 53))
            data, _ = sock.recvfrom(512)
        response_time = (time.time() - start) * 1000  # ms
        ip, ttl, status = parse_dns_response(data)
        return ip, ttl, status, response_time
    except socket.timeout:
        return None, None, 'TIMEOUT', (time.time() - start) * 1000
    except Exception as e:
        return None, None, f'ERROR: {e}', (time.time() - start) * 1000 