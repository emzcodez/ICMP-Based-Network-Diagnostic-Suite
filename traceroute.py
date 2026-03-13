import socket
def traceroute(host):
    dest = socket.gethostbyname(host)
    max_hops = 30
    port = 33434
    print("\nTraceroute to", host)

    for ttl in range(1, max_hops + 1):

        recv_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_ICMP
        )

        send_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )

        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

        recv_socket.bind(("", port))
        recv_socket.settimeout(2)
        send_socket.sendto(b"", (host, port))
        addr = None
        try:
            data, addr = recv_socket.recvfrom(512)
            print(ttl, addr[0])

        except socket.timeout:
            print(ttl, "*")

        recv_socket.close()
        send_socket.close()

        if addr and addr[0] == dest:
            break
