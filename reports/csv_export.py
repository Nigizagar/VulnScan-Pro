import csv
import io

def generate_csv(scan_data, target_name):
    """Menghasilkan file CSV dari data scan dalam bentuk string/buffer."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Port', 'State', 'Service', 'Banner', 'HTTP Server', 'HTTP Status'])
    
    for port in scan_data:
        writer.writerow([
            port.port, 
            port.state, 
            port.service, 
            port.banner, 
            port.http_server, 
            port.http_status
        ])
    return output.getvalue()