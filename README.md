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

- **Python 3.6+**
- **Administrator/Root privileges** (required for raw socket access)
- **Linux/macOS** (recommended) or Windows with appropriate permissions

## Installation

1. Clone or download this repository
2. No additional dependencies required (uses Python standard library only)

## Usage

### Basic Usage

```bash
# Ping a single host
sudo python3 main.py google.com

# Ping multiple hosts
sudo python3 main.py google.com github.com 8.8.8.8
```

**Note:** `sudo` is required on Linux/macOS for raw socket access. On Windows, run as Administrator.

### Advanced Usage

```bash
# Send 10 pings with 3-second timeout
sudo python3 main.py -c 10 -t 3.0 google.com

# Use custom TTL of 30 hops
sudo python3 main.py --ttl 30 google.com

# Simulate 20% packet loss for testing
sudo python3 main.py -l 0.2 google.com

# Combine multiple options
sudo python3 main.py -c 8 -t 1.5 --ttl 50 -l 0.15 cloudflare.com
```

### CLI Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `hosts` | - | Target host(s) to ping | (mandatory) |
| `--count` | `-c` | Number of ping requests | 4 |
| `--timeout` | `-t` | Timeout in seconds per ping | 2.0 |
| `--ttl` | - | Time To Live value | 64 |
| `--loss` | `-l` | Packet loss simulation rate | 0.0 |

### Get Help

```bash
python3 main.py -h
```

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
5. Increment TTL and repeat until the destination is reached (ICMP Echo Reply received)

This reveals each **hop** (router) along the path to the destination, up to a maximum of **30 hops**.

**Customization:**
- The **starting TTL** for ping can be customized using `--ttl`
- Lower TTL values may cause packets to expire before reaching the destination
- Useful for testing network behavior at different hop distances

### 6. Multi-Destination Support
The tool accepts **multiple hosts as input** and performs diagnostics for each host sequentially.

Example:
```bash
sudo python3 main.py google.com github.com cloudflare.com
```

Each host gets:
- Its own ping sequence
- RTT statistics
- Complete traceroute

### 7. Security Implementation (HMAC-SHA256)

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

**Secret Key:** `b"343_332_344"` (defined in `ICMP_ping.py`)

### 8. Packet Loss Simulation
The tool includes a **packet loss simulation feature** for testing and debugging purposes.

**Usage:**
```bash
sudo python3 main.py -l 0.2 google.com  # 20% packet loss
```

**How it works:**
- Before sending each packet, a random number is generated
- If the random value is less than the loss rate, the packet is "dropped"
- The dropped packet never gets sent, simulating real network packet loss

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

## Project Structure

- **`main.py`** - Orchestrates the program flow, handles user input, and displays results
- **`icmp_ping.py`** - Core ping functionality including packet creation, HMAC signing, and RTT measurement
- **`traceroute.py`** - Implements hop-by-hop route discovery using TTL manipulation
- **`stats.py`** - Computes statistics (min/max/avg RTT, packet loss percentage)
- **`README.md`** - This file

## Execution Flow

```
1. Parse CLI arguments (hosts, count, timeout, TTL, loss rate)
2. For each destination host:
   ├─→ Resolve hostname to IP address
   ├─→ Send ICMP Echo Requests (with custom TTL, timeout, loss simulation)
   ├─→ Measure RTT for each reply
   ├─→ Calculate packet loss statistics
   ├─→ Perform traceroute (TTL 1 → 30, discover each hop)
   └─→ Display results
3. Exit
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

## Limitations and Considerations

⚠️ **Requires elevated privileges** - Raw sockets need root/admin access  
⚠️ **Firewall interference** - Some firewalls block ICMP packets  
⚠️ **No IPv6 support** - Currently only supports IPv4 addresses  
⚠️ **Platform-dependent** - Best on Linux/macOS; Windows may have limitations  
⚠️ **Network restrictions** - Some networks/ISPs filter or rate-limit ICMP traffic  

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
