import sys
import socket
import time
from icmp_ping import ping
from stats import compute_stats
from traceroute import traceroute

def run_ping(host):
    try:    #in case user enters a bad hostname (which cant be resolved)
        dest = socket.gethostbyname(host)
    except socket.gaierror:
        print("Invalid host")
        return
    print(f"\nPinging {host} [{dest}]")   #Resolving hostname -> ip
    results = []
    for i in range(4):

        rtt = ping(host)

        if rtt:
            print("Reply:", round(rtt,2), "ms")
        else:
            print("Request timed out")

        results.append(rtt)
        time.sleep(1)   #waiting for a while between pings

    stats = compute_stats(results)

    print("\nStatistics")
    print("Sent:", stats["sent"])
    print("Received:", stats["received"])
    print("Packet Loss:", stats["loss"], "%")
    print("Average RTT:", stats["avg_rtt"], "ms")
    print("Min RTT:", stats["min_rtt"], "ms")
    print("Max RTT:", stats["max_rtt"], "ms")

    traceroute(host)

if __name__ == "__main__":
    if len(sys.argv) < 2:   #making sure user runs program w arguments
        print("Usage: python3 main.py <host1> <host2> ...")
        sys.exit(1)

    hosts = sys.argv[1:]

    for host in hosts:
        run_ping(host)
