import socket

def detect_service(port):
    """Mendeteksi service berdasarkan nomor port (IANA fallback)."""
    try:
        service_name = socket.getservbyport(port, "tcp")
        return service_name
    except OSError:
        # Fallback common ports jika tidak terdeteksi oleh OS
        common_ports = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
            443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
            5432: "PostgreSQL", 8080: "HTTP-Proxy"
        }
        return common_ports.get(port, "Unknown")