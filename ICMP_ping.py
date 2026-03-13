import socket
import struct
import time
import os
import hmac
import hashlib

ICMP_ECHO_REQUEST = 8
SECRET_KEY = b"my_super_secret_key"

def checksum(source_string):
    sum = 0
    count_to = (len(source_string) // 2) * 2
    count = 0
    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff
        count = count + 2
    if count_to < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_packet(pid):
    # Using '!' for Network Byte Order (Big Endian)
    # Header: type (1b), code (1b), checksum (2b), id (2b), sequence (2b)
    header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, 0, pid, 1)
    
    timestamp_data = struct.pack("d", time.time())
    signature = hmac.new(SECRET_KEY, timestamp_data, hashlib.sha256).digest()
    payload = timestamp_data + signature
    
    # Calculate checksum and repack header
    my_checksum = checksum(header + payload)
    header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, pid, 1)
    
    return header + payload

def ping(host):
    try:
        dest = socket.gethostbyname(host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except (PermissionError, socket.gaierror):
        return None

    try:
        pid = os.getpid() & 0xFFFF
        packet = create_packet(pid)
        sock.settimeout(2)
        start = time.time()
        sock.sendto(packet, (dest, 0))

        while True:
            data, addr = sock.recvfrom(1024)
            
            # ICMP header starts after the IP header (usually 20 bytes)
            ip_header_len = (data[0] & 0x0F) * 4
            icmp_header = data[ip_header_len:ip_header_len + 8]
            payload = data[ip_header_len + 8:]

            # Unpack using Network Byte Order '!'
            icmp_type, code, chk, packet_id, seq = struct.unpack("!bbHHh", icmp_header)

            # Type 0 is Echo Reply. ID must match our PID.
            if icmp_type == 0 and packet_id == pid:
                timestamp_data = payload[:8]
                received_sig = payload[8:40]
                expected_sig = hmac.new(SECRET_KEY, timestamp_data, hashlib.sha256).digest()

                if hmac.compare_digest(received_sig, expected_sig):
                    return (time.time() - start) * 1000
    except socket.timeout:
        return None
    finally:
        sock.close()
