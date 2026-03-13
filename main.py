import sys
from icmp_ping import ping
from stats import compute_stats
from traceroute import traceroute

def run_ping(host):
    print("\nPinging", host)
    results = []
    for i in range(4):

        rtt = ping(host)

        if rtt:
            print("Reply:", round(rtt,2), "ms")
        else:
            print("Request timed out")

        results.append(rtt)

    stats = compute_stats(results)

    print("\nStatistics")
    print("Sent:", stats["sent"])
    print("Received:", stats["received"])
    print("Packet Loss:", stats["loss"], "%")
    print("Average RTT:", stats["avg_rtt"], "ms")

    traceroute(host)

if __name__ == "__main__":

    hosts = sys.argv[1:]

    for host in hosts:
        run_ping(host)
