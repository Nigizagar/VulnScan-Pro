import requests
import urllib3

# Disable insecure request warning untuk port 443 tanpa SSL valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_http(ip, port):
    """Menganalisis HTTP Headers jika port adalah web port."""
    if port not in [80, 443, 8080, 8443]:
        return None, None

    protocol = "https" if port in [443, 8443] else "http"
    url = f"{protocol}://{ip}:{port}"
    
    try:
        response = requests.head(url, timeout=3, verify=False, allow_redirects=True)
        server = response.headers.get('Server', 'Unknown Web Server')
        status_code = str(response.status_code)
        return server, status_code
    except requests.exceptions.RequestException:
        return "Unreachable", "N/A"