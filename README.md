
# ICMP-Based Network Diagnostic Suite

## Overview
This project implements a **network diagnostic tool** that combines the functionality of **Ping** and **Traceroute** using **raw ICMP sockets**. The tool sends and receives ICMP packets directly to analyze connectivity, latency, and routing paths between the local machine and destination hosts.

The program measures **round‑trip time (RTT)**, calculates **packet loss**, and discovers the **network route (hops)** to a destination by manipulating the **TTL (Time-To-Live)** field in IP packets.

## Core Functionality

### 1. Raw ICMP Socket Communication
The program uses **raw sockets** to manually create and transmit ICMP packets, specifically:

- ICMP Echo Request  
- ICMP Echo Reply  
- ICMP Time Exceeded  

This allows direct interaction with the network layer.


### 2. Ping Implementation
The tool sends **ICMP Echo Requests** to a host and waits for **Echo Replies** to determine:

- Whether the host is reachable  
- The **round‑trip time (RTT)** for each packet  


### 3. RTT Measurement
The program records the time when a packet is sent and when the reply is received to calculate latency.

`RTT = time_received − time_sent`

### 4. Packet Loss Calculation
Multiple ping requests are sent and the tool computes packet loss using:

`Packet Loss (%) = (Lost Packets / Sent Packets) × 100`


### 5. Traceroute (TTL Manipulation)
The traceroute component discovers the network path to a destination by increasing the **TTL value** of packets.

Each router decreases TTL by **1**. When TTL reaches **0**, the router returns an **ICMP Time Exceeded** message, allowing the program to identify that hop.


### 6. Multi-Destination Support
The tool accepts **multiple hosts as input** and performs diagnostics for each host sequentially.

Example command:

```
python main.py google.com github.com
```

### 7. **Security Implementation (HMAC-SHA256)**
Payload Authentication: To satisfy security requirements, every outgoing packet contains a payload signed with an HMAC-SHA256 signature.

Verification: The tool verifies the signature of the reply against a shared secret key to prevent packet spoofing and tampering.

## Project Structure

```
network-diagnostic-tool
│
├── main.py        # Program entry point
├── icmp_ping.py   # ICMP ping implementation
├── traceroute.py  # TTL-based route discovery
├── stats.py       # RTT and packet-loss calculations
└── README.md
```

## Execution Flow

1. User provides one or more destination hosts  
2. The program resolves each hostname to an IP address  
3. ICMP Echo Requests are sent using raw sockets  
4. RTT is measured for each reply received  
5. Packet loss statistics are calculated  
6. TTL values are incremented to perform traceroute and discover network hops  
7. Results are printed for each destination
