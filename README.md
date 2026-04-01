# ICMP-Based Network Diagnostic Suite

## Overview
This project implements a **network diagnostic tool** that combines the functionality of **Ping** and **Traceroute** using **raw ICMP sockets**. The tool sends and receives ICMP packets directly to analyze connectivity, latency, and routing paths between the local machine and destination hosts.

The program measures **round-trip time (RTT)**, calculates **packet loss**, and discovers the **network route (hops)** to a destination by manipulating the **TTL (Time-To-Live)** field in IP packets.

## Features

- [x] **ICMP Ping** - Test host reachability and measure latency  
- [x] **Traceroute** - Discover the network path to destinations  
- [x] **RTT Statistics** - Min, max, and average round-trip times  
- [x] **Packet Loss Analysis** - Track and report lost packets  
- [x] **HMAC-SHA256 Security** - Payload authentication to prevent spoofing  
- [x] **Multi-Host Support** - Ping multiple destinations in one command  
- [x] **Customizable Parameters** - Adjust TTL, timeout, packet count, and simulate packet loss  

## Prerequisites

- **Python 3.6+** with **tkinter** module installed
- **Administrator/Root privileges** (required for raw socket access)
- **Linux/macOS** (recommended) or Windows with appropriate permissions

## Core Functionality

### 1. Raw ICMP Socket Communication
The program uses **raw sockets** (`SOCK_RAW`) to manually create and transmit ICMP packets, specifically:
- **ICMP Echo Request (Type 8)** - Sent to probe hosts  
- **ICMP Echo Reply (Type 0)** - Received from responding hosts  
- **ICMP Time Exceeded (Type 11)** - Received from intermediate routers during traceroute  

This allows direct interaction with the network layer, bypassing higher-level protocols.

### 2. Ping Implementation
The tool sends **ICMP Echo Requests** to a host and waits for **Echo Replies** to determine:
- Whether the host is **reachable**  
- The **round-trip time (RTT)** for each packet  
- **Packet loss** over multiple attempts  

Each packet includes:
- A unique **Process ID** for identification
- A **timestamp** for RTT calculation
- An **HMAC-SHA256 signature** for security

### 3. RTT Measurement
The program records the time when a packet is sent and when the reply is received to calculate latency:

```
RTT (ms) = (time_received − time_sent) × 1000
```

Statistics computed:
- **Average RTT** - Mean of all successful pings
- **Minimum RTT** - Best-case latency
- **Maximum RTT** - Worst-case latency

### 4. Packet Loss Calculation
Multiple ping requests are sent and the tool computes packet loss percentage:

```
Packet Loss (%) = (Packets Lost / Packets Sent) × 100
```

Packets are considered "lost" if:
- No reply is received within the timeout period
- The simulated packet loss feature randomly drops them (when `-l` is used)

### 5. Traceroute (TTL Manipulation)
The traceroute component discovers the network path to a destination by incrementally increasing the **TTL value** of outgoing packets.

**How it works:**
1. Start with TTL = 1
2. Send an ICMP Echo Request
3. The first router decrements TTL to 0 and returns **ICMP Time Exceeded**
4. Record the router's IP address and RTT
5. Increment TTL and repeat the iterative hops until the destination is reached (ICMP Echo Reply received)

This reveals each **hop** (router) along the path to the destination, up to a maximum of **30 hops**.

**Customization:**
- The **starting TTL** for ping can be customized using `--ttl`
- Lower TTL values may cause packets to expire before reaching the destination
- Useful for testing network behavior at different hop distances

### 6. Multi-Destination Support
The tool accepts **multiple hosts as input** and performs diagnostics for each host sequentially.

Each host gets:
- Its own ping sequence
- RTT statistics
- Complete traceroute

### 7. SSL Security Implementation (HMAC-SHA256)

**Payload Authentication:**  
Every outgoing packet contains a payload with:
1. **Timestamp** - The exact time the packet was created
2. **HMAC-SHA256 Signature** - A cryptographic hash of the timestamp using a secret key

**Verification Process:**
1. When a reply is received, the timestamp is extracted
2. The HMAC signature is recalculated using the same secret key
3. Signatures are compared using `hmac.compare_digest()` (timing-attack resistant)
4. Only packets with valid signatures are accepted

**Security Benefits:**
- Prevents **packet spoofing** (attackers can't forge valid replies)
- Detects **packet tampering** (modified packets fail verification)
- Ensures **data integrity** throughout transmission

### 8. Packet Loss Simulation
The tool includes a **packet loss simulation feature** for testing and debugging purposes.
Click on a packet to delete/loose it.

**Use cases:**
- Testing application resilience to network issues
- Simulating poor network conditions
- Debugging retry and timeout logic

### 9. Checksum Calculation
Every ICMP packet includes a **checksum** field to verify data integrity during transmission.

**Implementation:**
- Processes data in 16-bit (2-byte) chunks
- Sums all chunks with carry handling
- Computes one's complement of the final sum
- Byte-swaps to network byte order (Big Endian)

This ensures corrupted packets are detected and discarded by receiving hosts.

## Execution Flow

```
1. Processes each host sequentially
2. Shows progress: "HOST 1/3", "HOST 2/3", etc.
3. Displays separate statistics for each host
4. Summary shown at completion
```

## Technical Details

### Network Byte Order
All packet headers use **Big Endian** (network byte order):
```python
struct.pack("!bbHHh", ...)  # '!' enforces Big Endian
```

### Socket Configuration
```python
socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
```
- **AF_INET**: IPv4 addressing
- **SOCK_RAW**: Raw socket access (bypasses transport layer)
- **IPPROTO_ICMP**: ICMP protocol

### ICMP Packet Structure
```
IP Header (20 bytes) - Added by OS
├─ ICMP Header (8 bytes)
│  ├─ Type (1 byte): 8 for Echo Request, 0 for Echo Reply
│  ├─ Code (1 byte): 0
│  ├─ Checksum (2 bytes): Error detection
│  ├─ Identifier (2 bytes): Process ID
│  └─ Sequence (2 bytes): Packet sequence number
└─ Payload (variable)
   ├─ Timestamp (8 bytes): For RTT calculation
   └─ HMAC Signature (32 bytes): SHA-256 authentication
```

## Troubleshooting

### "Permission denied" error
**Solution:** Run with `sudo` (Linux/macOS) or as Administrator (Windows)

### "Invalid host" error
**Solution:** Check hostname spelling or use an IP address directly

### No replies received
**Possible causes:**
- Host is down or blocking ICMP
- Firewall is blocking packets
- TTL too low (packets expire before reaching destination)

### Timeout errors in traceroute
**Explanation:** Some routers don't respond to ICMP packets; shows as `*` in output
