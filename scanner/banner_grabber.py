import socket

def grab_banner(ip, port, timeout=2):
    """Mengambil banner dari service jaringan menggunakan socket."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        
        # Kirim dummy payload untuk memancing respons HTTP/HTTPS jika diperlukan
        if port in [80, 443, 8080]:
            s.send(b"HEAD / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
            
        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        
        # Ambil baris pertama saja untuk banner yang rapi
        if banner:
            return banner.split('\n')[0][:100] 
        return "No banner"
    except Exception:
        return "No banner"