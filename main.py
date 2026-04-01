import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import struct
import time
import os
import hmac
import hashlib
import threading
import random
from collections import deque

ICMP_ECHO_REQUEST = 8
SECRET_KEY = b"343_332_344"

class Packet:
    def __init__(self, canvas, start_x, start_y, end_x, end_y, packet_id, ttl):
        self.canvas = canvas
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.packet_id = packet_id
        self.ttl = ttl
        self.current_x = start_x
        self.current_y = start_y
        self.deleted = False
        
        self.circle = canvas.create_oval(
            start_x - 8, start_y - 8, start_x + 8, start_y + 8,
            fill='#4CAF50', outline='#2E7D32', width=2
        )
        self.text = canvas.create_text(
            start_x, start_y, text=str(packet_id), fill='white', font=('Arial', 8, 'bold')
        )
        
        canvas.tag_bind(self.circle, '<Button-1>', self.on_click)
        canvas.tag_bind(self.text, '<Button-1>', self.on_click)
        
    def on_click(self, event):
        if not self.deleted:
            self.deleted = True
            self.canvas.itemconfig(self.circle, fill='#F44336', outline='#C62828')
            self.canvas.after(100, self.remove)
            
    def animate_step(self, progress):
        if self.deleted:
            return False
            
        self.current_x = self.start_x + (self.end_x - self.start_x) * progress
        self.current_y = self.start_y + (self.end_y - self.start_y) * progress
        
        self.canvas.coords(
            self.circle,
            self.current_x - 8, self.current_y - 8,
            self.current_x + 8, self.current_y + 8
        )
        self.canvas.coords(self.text, self.current_x, self.current_y)
        return True
        
    def remove(self):
        self.canvas.delete(self.circle)
        self.canvas.delete(self.text)


class NetworkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Diagnostic Tool - Enhanced GUI")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        self.is_running = False
        self.packets = deque()
        self.packet_counter = 0
        self.custom_ttl = None
        self.server_running = False
        self.server_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        title_frame = tk.Frame(self.root, bg='#2196F3', height=60)
        title_frame.pack(fill='x')
        title_label = tk.Label(
            title_frame, text="🌐 Network Diagnostic Tool",
            font=('Arial', 18, 'bold'), bg='#2196F3', fg='white'
        )
        title_label.pack(pady=15)
        
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_panel_container = tk.Frame(main_container, bg='white', relief='raised', borderwidth=2)
        left_panel_container.pack(side='left', fill='both', padx=(0, 5), pady=0)
        
        canvas_left = tk.Canvas(left_panel_container, bg='white', highlightthickness=0, width=280)
        scrollbar = tk.Scrollbar(left_panel_container, orient='vertical', command=canvas_left.yview)
        scrollable_frame = tk.Frame(canvas_left, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_left.configure(scrollregion=canvas_left.bbox("all"))
        )
        
        canvas_left.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas_left.configure(yscrollcommand=scrollbar.set)
        
        canvas_left.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def on_mousewheel(event):
            canvas_left.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas_left.bind_all("<MouseWheel>", on_mousewheel)
        canvas_left.bind_all("<Button-4>", lambda e: canvas_left.yview_scroll(-1, "units"))
        canvas_left.bind_all("<Button-5>", lambda e: canvas_left.yview_scroll(1, "units"))
        
        left_panel = scrollable_frame
        
        input_frame = tk.LabelFrame(left_panel, text="Target Host", font=('Arial', 10, 'bold'), 
                                    bg='white', padx=10, pady=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            input_frame, text="Enter host(s) separated by commas:",
            bg='white', font=('Arial', 8), fg='#666'
        ).pack(anchor='w', pady=(0, 3))
        
        self.host_entry = tk.Entry(input_frame, font=('Arial', 11), width=25)
        self.host_entry.pack(fill='x', pady=5)
        self.host_entry.insert(0, "google.com")
        
        tk.Label(
            input_frame, text="Example: google.com, 8.8.8.8, github.com",
            bg='white', font=('Arial', 7, 'italic'), fg='#999'
        ).pack(anchor='w')
        
        ttl_frame = tk.LabelFrame(left_panel, text="TTL Configuration", 
                                  font=('Arial', 10, 'bold'), bg='white', padx=10, pady=10)
        ttl_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(ttl_frame, text="Custom TTL:", bg='white', font=('Arial', 9)).pack(anchor='w')
        
        ttl_control_frame = tk.Frame(ttl_frame, bg='white')
        ttl_control_frame.pack(fill='x', pady=5)
        
        self.ttl_var = tk.IntVar(value=64)
        self.ttl_slider = tk.Scale(
            ttl_control_frame, from_=1, to=255, orient='horizontal',
            variable=self.ttl_var, bg='white', length=180
        )
        self.ttl_slider.pack(side='left', fill='x', expand=True)
        
        self.ttl_label = tk.Label(ttl_control_frame, text="64", bg='white', 
                                  font=('Arial', 10, 'bold'), width=4)
        self.ttl_label.pack(side='left', padx=5)
        
        self.ttl_var.trace('w', lambda *args: self.ttl_label.config(text=str(self.ttl_var.get())))
        
        self.use_custom_ttl = tk.BooleanVar(value=False)
        ttl_check = tk.Checkbutton(
            ttl_frame, text="Use custom TTL", variable=self.use_custom_ttl,
            bg='white', font=('Arial', 9)
        )
        ttl_check.pack(anchor='w')
        
        loss_frame = tk.LabelFrame(left_panel, text="Packet Loss Simulation", 
                                   font=('Arial', 10, 'bold'), bg='white', padx=10, pady=10)
        loss_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            loss_frame, text="Click on packets to simulate loss!",
            bg='white', fg='#F44336', font=('Arial', 9, 'italic')
        ).pack(pady=5)
        
        button_frame = tk.Frame(left_panel, bg='white')
        button_frame.pack(fill='x', padx=10, pady=20)
        
        self.ping_btn = tk.Button(
            button_frame, text="Start Ping", command=self.start_ping,
            bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'),
            relief='raised', borderwidth=2, cursor='hand2'
        )
        self.ping_btn.pack(fill='x', pady=5)
        
        self.traceroute_btn = tk.Button(
            button_frame, text="Start Traceroute", command=self.start_traceroute,
            bg='#2196F3', fg='white', font=('Arial', 11, 'bold'),
            relief='raised', borderwidth=2, cursor='hand2'
        )
        self.traceroute_btn.pack(fill='x', pady=5)
        
        self.stop_btn = tk.Button(
            button_frame, text="Stop", command=self.stop_operation,
            bg='#F44336', fg='white', font=('Arial', 11, 'bold'),
            relief='raised', borderwidth=2, cursor='hand2', state='disabled'
        )
        self.stop_btn.pack(fill='x', pady=5)
        
        server_frame = tk.LabelFrame(left_panel, text="ICMP Server Mode", 
                                     font=('Arial', 10, 'bold'), bg='white', padx=10, pady=10)
        server_frame.pack(fill='x', padx=10, pady=20)
        
        tk.Label(
            server_frame, text="Run as ICMP server to simulate\nhops and network conditions",
            bg='white', font=('Arial', 9), justify='left'
        ).pack(pady=5)
        
        self.server_btn = tk.Button(
            server_frame, text="Start Server", command=self.toggle_server,
            bg='#FF9800', fg='white', font=('Arial', 11, 'bold'),
            relief='raised', borderwidth=2, cursor='hand2'
        )
        self.server_btn.pack(fill='x', pady=5)
        
        self.server_status = tk.Label(
            server_frame, text="Server: Stopped", bg='white', 
            fg='#F44336', font=('Arial', 9, 'bold')
        )
        self.server_status.pack(pady=5)
        
        right_panel = tk.Frame(main_container, bg='white', relief='raised', borderwidth=2)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        canvas_frame = tk.LabelFrame(right_panel, text="Packet Transmission Visualization", 
                                     font=('Arial', 10, 'bold'), bg='white')
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#E3F2FD', height=250)
        self.canvas.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.draw_network_diagram()
        
        output_frame = tk.LabelFrame(right_panel, text="Console Output", 
                                     font=('Arial', 10, 'bold'), bg='white')
        output_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, height=12, font=('Courier', 9), bg='#263238', fg='#00FF00',
            insertbackground='white'
        )
        self.output_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.status_bar = tk.Label(
            self.root, text="Ready", bg='#37474F', fg='white',
            font=('Arial', 9), anchor='w', padx=10
        )
        self.status_bar.pack(side='bottom', fill='x')
        
    def draw_network_diagram(self):
        self.canvas.delete('all')
        
        width = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 700
        height = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 250
        
        self.source_x = 80
        self.source_y = height // 2
        self.canvas.create_rectangle(
            self.source_x - 30, self.source_y - 25,
            self.source_x + 30, self.source_y + 25,
            fill='#1976D2', outline='#0D47A1', width=2
        )
        self.canvas.create_text(
            self.source_x, self.source_y, text="SOURCE", fill='white', font=('Arial', 9, 'bold')
        )
        
        self.dest_x = width - 80
        self.dest_y = height // 2
        self.canvas.create_rectangle(
            self.dest_x - 30, self.dest_y - 25,
            self.dest_x + 30, self.dest_y + 25,
            fill='#388E3C', outline='#1B5E20', width=2
        )
        self.canvas.create_text(
            self.dest_x, self.dest_y, text="DEST", fill='white', font=('Arial', 9, 'bold')
        )
        
        self.canvas.create_line(
            self.source_x + 30, self.source_y,
            self.dest_x - 30, self.dest_y,
            fill='#90A4AE', width=2, dash=(5, 3)
        )
        
        legend_x = 20
        legend_y = 20
        self.canvas.create_oval(legend_x, legend_y, legend_x + 16, legend_y + 16, 
                                fill='#4CAF50', outline='#2E7D32', width=2)
        self.canvas.create_text(legend_x + 30, legend_y + 8, text="Active Packet", 
                                anchor='w', font=('Arial', 8))
        
        self.canvas.create_oval(legend_x, legend_y + 25, legend_x + 16, legend_y + 41, 
                                fill='#F44336', outline='#C62828', width=2)
        self.canvas.create_text(legend_x + 30, legend_y + 33, text="Lost Packet (Click to delete)", 
                                anchor='w', font=('Arial', 8))
        
    def log(self, message):
        self.output_text.insert('end', message + '\n')
        self.output_text.see('end')
        self.root.update_idletasks()
        
    def create_packet(self, pid, ttl=None):
        header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, 0, pid, 1)
        
        timestamp_data = struct.pack("d", time.time())
        signature = hmac.new(SECRET_KEY, timestamp_data, hashlib.sha256).digest()
        payload = timestamp_data + signature
        
        def checksum(data):
            sum_val = 0
            count_to = (len(data) // 2) * 2
            count = 0
            while count < count_to:
                this_val = data[count + 1] * 256 + data[count]
                sum_val = sum_val + this_val
                sum_val = sum_val & 0xffffffff
                count = count + 2
            if count_to < len(data):
                sum_val = sum_val + data[len(data) - 1]
                sum_val = sum_val & 0xffffffff
            sum_val = (sum_val >> 16) + (sum_val & 0xffff)
            sum_val = sum_val + (sum_val >> 16)
            answer = ~sum_val
            answer = answer & 0xffff
            answer = answer >> 8 | (answer << 8 & 0xff00)
            return answer
        
        my_checksum = checksum(header + payload)
        header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, pid, 1)
        
        return header + payload
    
    def animate_packet(self, packet, duration=3.0):
        steps = 60
        delay = int(duration * 1000 / steps)
        
        def step(i):
            if i <= steps:
                progress = i / steps
                if packet.animate_step(progress):
                    self.root.after(delay, lambda: step(i + 1))
                else:
                    return
            else:
                packet.remove()
                
        step(0)
    
    def ping_with_visualization(self, host, count=4):
        try:
            dest = socket.gethostbyname(host)
        except socket.gaierror:
            self.log(f"❌ Error: Could not resolve host {host}")
            return
        
        self.log(f"\n🔍 Pinging {host} [{dest}]")
        self.log(f"{'='*50}")
        
        results = []
        
        for i in range(count):
            if not self.is_running:
                break
                
            self.packet_counter += 1
            ttl = self.ttl_var.get() if self.use_custom_ttl.get() else 64
            
            packet = Packet(
                self.canvas,
                self.source_x + 30, self.source_y,
                self.dest_x - 30, self.dest_y,
                self.packet_counter, ttl
            )
            
            self.animate_packet(packet, duration=3.0)
            
            packet_deleted = False
            for check in range(30):
                time.sleep(0.1)
                if packet.deleted:
                    packet_deleted = True
                    break
            
            if packet_deleted:
                self.log(f"📦 Packet #{self.packet_counter}: ❌ SIMULATED LOSS (clicked)")
                results.append(None)
            else:
                rtt = self.ping_host(host, ttl)
                
                if rtt:
                    self.log(f"📦 Packet #{self.packet_counter}: ✅ Reply in {rtt:.2f} ms (TTL={ttl})")
                    results.append(rtt)
                else:
                    self.log(f"📦 Packet #{self.packet_counter}: ⏱️ Request timed out")
                    results.append(None)
            
            time.sleep(0.5)
        
        self.compute_and_display_stats(results)
        
    def ping_host(self, host, ttl=64):
        try:
            dest = socket.gethostbyname(host)
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        except (PermissionError, socket.gaierror):
            return None

        try:
            pid = os.getpid() & 0xFFFF
            packet = self.create_packet(pid, ttl)
            sock.settimeout(2)
            start = time.time()
            sock.sendto(packet, (dest, 0))

            while True:
                data, addr = sock.recvfrom(1024)
                
                ip_header_len = (data[0] & 0x0F) * 4
                icmp_header = data[ip_header_len:ip_header_len + 8]
                payload = data[ip_header_len + 8:]

                icmp_type, code, chk, packet_id, seq = struct.unpack("!bbHHh", icmp_header)

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
    
    def compute_and_display_stats(self, results):
        sent = len(results)
        received = len([r for r in results if r is not None])
        loss = ((sent - received) / sent) * 100
        rtts = [r for r in results if r]
        
        avg = sum(rtts) / len(rtts) if rtts else 0
        min_rtt = min(rtts) if rtts else 0
        max_rtt = max(rtts) if rtts else 0
        
        self.log(f"\n📊 Statistics:")
        self.log(f"{'='*50}")
        self.log(f"Sent: {sent} | Received: {received} | Loss: {loss:.1f}%")
        self.log(f"RTT - Min: {min_rtt:.2f}ms | Avg: {avg:.2f}ms | Max: {max_rtt:.2f}ms")
        
    def traceroute_with_visualization(self, host):
        try:
            dest_ip = socket.gethostbyname(host)
        except socket.gaierror:
            self.log(f"❌ Error: Could not resolve host {host}")
            return

        max_hops = 30
        pid = os.getpid() & 0xFFFF
        
        self.log(f"\n🛤️ Traceroute to {host} ({dest_ip})")
        self.log(f"{'='*50}")

        for ttl in range(1, max_hops + 1):
            if not self.is_running:
                break
                
            self.packet_counter += 1
            packet = Packet(
                self.canvas,
                self.source_x + 30, self.source_y,
                self.dest_x - 30, self.dest_y,
                self.packet_counter, ttl
            )
            self.animate_packet(packet, duration=2.5)
            
            packet_deleted = False
            for check in range(25):
                time.sleep(0.1)
                if packet.deleted:
                    packet_deleted = True
                    break
            
            if packet_deleted:
                self.log(f"{ttl:2d}. ❌ SIMULATED LOSS (clicked)")
                continue
                
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                sock.settimeout(2.0)
                
                packet_data = self.create_packet(pid, ttl)
                sock.sendto(packet_data, (dest_ip, 1))
                
                start_time = time.time()
                data, addr = sock.recvfrom(1024)
                duration = (time.time() - start_time) * 1000
                
                ip_header_len = (data[0] & 0x0F) * 4
                icmp_type = data[ip_header_len]
                
                if icmp_type == 11:
                    self.log(f"{ttl:2d}. {addr[0]:15s} {duration:7.2f} ms")
                elif icmp_type == 0:
                    self.log(f"{ttl:2d}. {addr[0]:15s} {duration:7.2f} ms ✅ (Reached)")
                    self.log("🎯 Trace complete!")
                    return
                else:
                    self.log(f"{ttl:2d}. {addr[0]:15s} {duration:7.2f} ms (Type {icmp_type})")

            except (socket.timeout, TimeoutError):
                self.log(f"{ttl:2d}. * * * (timeout)")
            except Exception as e:
                self.log(f"{ttl:2d}. Error: {e}")
            finally:
                if sock:
                    sock.close()
                time.sleep(0.3)
    
    def start_ping(self):
        host_input = self.host_entry.get().strip()
        if not host_input:
            messagebox.showwarning("Input Required", "Please enter a host!")
            return
        
        hosts = [h.strip() for h in host_input.split(',') if h.strip()]
        
        if len(hosts) == 0:
            messagebox.showwarning("Input Required", "Please enter at least one host!")
            return
        
        self.is_running = True
        self.ping_btn.config(state='disabled')
        self.traceroute_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        if len(hosts) == 1:
            self.status_bar.config(text=f"Pinging {hosts[0]}...")
        else:
            self.status_bar.config(text=f"Pinging {len(hosts)} hosts...")
        
        self.output_text.delete(1.0, 'end')
        
        def run():
            try:
                for i, host in enumerate(hosts):
                    if not self.is_running:
                        break
                    
                    if len(hosts) > 1:
                        self.log(f"\n{'='*50}")
                        self.log(f"HOST {i+1}/{len(hosts)}: {host}")
                        self.log(f"{'='*50}")
                    
                    self.ping_with_visualization(host)
                    
                    if i < len(hosts) - 1 and self.is_running:
                        time.sleep(1)
                
                if len(hosts) > 1 and self.is_running:
                    self.log(f"\n{'='*50}")
                    self.log(f"✅ Completed pinging all {len(hosts)} hosts")
                    self.log(f"{'='*50}")
                    
            except PermissionError:
                self.log("❌ Error: This tool requires root/administrator privileges!")
                messagebox.showerror("Permission Error", 
                                   "Please run this program with sudo/administrator privileges!")
            finally:
                self.is_running = False
                self.ping_btn.config(state='normal')
                self.traceroute_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
                self.status_bar.config(text="Ready")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def start_traceroute(self):
        host_input = self.host_entry.get().strip()
        if not host_input:
            messagebox.showwarning("Input Required", "Please enter a host!")
            return
        
        hosts = [h.strip() for h in host_input.split(',') if h.strip()]
        
        if len(hosts) == 0:
            messagebox.showwarning("Input Required", "Please enter at least one host!")
            return
        
        self.is_running = True
        self.ping_btn.config(state='disabled')
        self.traceroute_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        if len(hosts) == 1:
            self.status_bar.config(text=f"Tracing route to {hosts[0]}...")
        else:
            self.status_bar.config(text=f"Tracing route to {len(hosts)} hosts...")
        
        self.output_text.delete(1.0, 'end')
        
        def run():
            try:
                for i, host in enumerate(hosts):
                    if not self.is_running:
                        break
                    
                    if len(hosts) > 1:
                        self.log(f"\n{'='*50}")
                        self.log(f"HOST {i+1}/{len(hosts)}: {host}")
                        self.log(f"{'='*50}")
                    
                    self.traceroute_with_visualization(host)
                    
                    if i < len(hosts) - 1 and self.is_running:
                        time.sleep(1)
                
                if len(hosts) > 1 and self.is_running:
                    self.log(f"\n{'='*50}")
                    self.log(f"✅ Completed traceroute for all {len(hosts)} hosts")
                    self.log(f"{'='*50}")
                    
            except PermissionError:
                self.log("❌ Error: This tool requires root/administrator privileges!")
                messagebox.showerror("Permission Error", 
                                   "Please run this program with sudo/administrator privileges!")
            finally:
                self.is_running = False
                self.ping_btn.config(state='normal')
                self.traceroute_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
                self.status_bar.config(text="Ready")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop_operation(self):
        self.is_running = False
        self.status_bar.config(text="Stopped")
        self.log("\n⏹️ Operation stopped by user")
    
    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        self.server_running = True
        self.server_btn.config(text="Stop Server", bg='#F44336')
        self.server_status.config(text="Server: Running", fg='#4CAF50')
        self.status_bar.config(text="ICMP Server running...")
        self.log("\n🖥️ ICMP Server Started")
        self.log(f"{'='*50}")
        
        def run_server():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                self.log("✅ Server listening for ICMP packets...")
                
                hop_tracker = {}
                
                while self.server_running:
                    try:
                        sock.settimeout(1.0)
                        data, addr = sock.recvfrom(1024)
                        
                        if not self.server_running:
                            break
                        
                        ip_ttl = data[8]
                        ip_header_len = (data[0] & 0x0F) * 4
                        icmp_header = data[ip_header_len:ip_header_len + 8]
                        payload = data[ip_header_len + 8:]
                        
                        icmp_type, code, recv_checksum, packet_id, seq = struct.unpack("!bbHHh", icmp_header)
                        
                        if icmp_type != 8:
                            continue
                        
                        self.log(f"📨 Received packet from {addr[0]} (TTL={ip_ttl})")
                        
                        if len(payload) >= 12:
                            timestamp = payload[:8]
                            mode_data = payload[8:12] if len(payload) >= 12 else b'\x00\x00\x00\x00'
                            received_sig = payload[12:] if len(payload) > 12 else b''
                            
                            if len(mode_data) == 4:
                                mode = struct.unpack("i", mode_data)[0]
                            else:
                                mode = 0
                            
                            client_ip = addr[0]
                            if client_ip not in hop_tracker:
                                hop_tracker[client_ip] = 1
                            else:
                                hop_tracker[client_ip] += 1
                            
                            current_hop = hop_tracker[client_ip]
                            
                            if current_hop <= 3:
                                self.log(f"   🔄 Simulating hop {current_hop} (Time Exceeded)")
                                reply_type = 11
                                reply_code = 0
                            else:
                                self.log(f"   ✅ Destination reached (Echo Reply)")
                                reply_type = 0
                                reply_code = 0
                            
                            if mode == 1:
                                self.log(f"   ⏱️ Mode 1: Simulating delay...")
                                time.sleep(1)
                            elif mode == 2:
                                self.log(f"   ❌ Mode 2: Dropping packet")
                                continue
                            elif mode == 3:
                                if random.random() < 0.5:
                                    self.log(f"   🎲 Mode 3: Random drop")
                                    continue
                        else:
                            reply_type = 0
                            reply_code = 0
                        
                        reply_header = struct.pack("!bbHHh", reply_type, reply_code, 0, packet_id, seq)
                        packet = reply_header + payload
                        
                        def calc_checksum(data):
                            s = 0
                            for i in range(0, len(data) - 1, 2):
                                s += (data[i] << 8) + data[i+1]
                            if len(data) % 2:
                                s += data[-1] << 8
                            s = (s >> 16) + (s & 0xffff)
                            s += (s >> 16)
                            return ~s & 0xffff
                        
                        chk = calc_checksum(packet)
                        reply_header = struct.pack("!bbHHh", reply_type, reply_code, chk, packet_id, seq)
                        reply_packet = reply_header + payload
                        
                        sock.sendto(reply_packet, addr)
                        self.log(f"   📤 Reply sent!\n")
                        
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.server_running:
                            self.log(f"⚠️ Server error: {e}")
                
                sock.close()
                self.log("🛑 Server stopped")
                
            except PermissionError:
                self.log("❌ Server requires root/administrator privileges!")
                messagebox.showerror("Permission Error", 
                                   "Server mode requires sudo/administrator privileges!")
                self.server_running = False
                self.server_btn.config(text="Start Server", bg='#FF9800')
                self.server_status.config(text="Server: Stopped", fg='#F44336')
            except Exception as e:
                self.log(f"❌ Server error: {e}")
                self.server_running = False
                self.server_btn.config(text="Start Server", bg='#FF9800')
                self.server_status.config(text="Server: Stopped", fg='#F44336')
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
    
    def stop_server(self):
        self.server_running = False
        self.server_btn.config(text="Start Server", bg='#FF9800')
        self.server_status.config(text="Server: Stopped", fg='#F44336')
        self.status_bar.config(text="Ready")
        self.log("\n🛑 Stopping server...")


def main():
    root = tk.Tk()
    app = NetworkGUI(root)
    
    def on_resize(event):
        app.draw_network_diagram()
    
    app.canvas.bind('<Configure>', on_resize)
    
    root.mainloop()


if __name__ == "__main__":
    main()
