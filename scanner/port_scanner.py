import socket
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Cari path ke folder 'VulnScan Pro' (dua tingkat di atas file ini)
# dan masukkan ke sys.path agar Python tahu di mana folder 'scanner' berada
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Sekarang import akan dijamin berhasil secara absolut
from scanner.banner_grabber import grab_banner
from scanner.service_detector import detect_service
from scanner.http_analyzer import analyze_http

class ScannerCore:
    def __init__(self, target, start_port, end_port, threads=50):
        self.target = target
        self.start_port = start_port
        self.end_port = end_port
        self.threads = threads
        self.results = []
        
        # Resolving target ke IP
        try:
            self.target_ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.target_ip = None

    def scan_port(self, port):
        """Memeriksa satu port dan mengumpulkan enumerasi jika terbuka."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.target_ip, port))
            
            if result == 0:
                service = detect_service(port)
                banner = grab_banner(self.target_ip, port)
                http_server, http_status = analyze_http(self.target_ip, port)
                
                self.results.append({
                    "port": port,
                    "state": "Open",
                    "service": service,
                    "banner": banner,
                    "http_server": http_server,
                    "http_status": http_status
                })
            sock.close()
        except Exception as e:
            pass # Skip jika error untuk mempercepat scan

    def run_scan(self):
        """Menjalankan scan dengan multithreading."""
        if not self.target_ip:
            return [] # Invalid target

        ports_to_scan = range(self.start_port, self.end_port + 1)
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self.scan_port, ports_to_scan)
            
        # Urutkan hasil berdasarkan port number
        self.results = sorted(self.results, key=lambda x: x['port'])
        return self.results