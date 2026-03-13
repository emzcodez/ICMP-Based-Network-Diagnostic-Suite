import socket
import os
import struct
import time
from icmp_ping import create_packet

def traceroute(host):
    try:
        dest_ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Error: Could not resolve host {host}")
        return

    max_hops = 30
    pid = os.getpid() & 0xFFFF
    
    print(f"\nTraceroute to {host} ({dest_ip}) using ICMP:")

    for ttl in range(1, max_hops + 1):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            sock.settimeout(2.0)
            
            packet = create_packet(pid)
            sock.sendto(packet, (dest_ip, 1))
            
            start_time = time.time()
            data, addr = sock.recvfrom(1024)
            duration = (time.time() - start_time) * 1000
            
            # Robustness: Determine if we hit a router or the destination
            ip_header_len = (data[0] & 0x0F) * 4
            icmp_type = data[ip_header_len]
            
            if icmp_type == 11: # ICMP Time Exceeded (Intermediate Hop)
                print(f"{ttl}\t{addr[0]}\t{duration:.2f} ms")
            elif icmp_type == 0: # ICMP Echo Reply (Final Destination)
                print(f"{ttl}\t{addr[0]}\t{duration:.2f} ms\t(Reached)")
                print("Trace complete.")
                return
            else:
                print(f"{ttl}\t{addr[0]}\t{duration:.2f} ms\t(Type {icmp_type})")

        except (socket.timeout, TimeoutError):
            # This fixes the specific crash in your screenshot
            print(f"{ttl}\t*")
        except Exception as e:
            print(f"{ttl}\tError: {e}")
        finally:
            if sock:
                sock.close()
