import os
import sys

# Memaksa Python memasukkan direktori tempat app.py berada ke dalam pencarian modul
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
import re
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database.models import db, ScanTarget, ScanHistory, PortDetails
from scanner.port_scanner import ScannerCore
from reports.csv_export import generate_csv
from reports.pdf_export import generate_pdf
import io

# ... sisa kode app.py ke bawah tetap sama ...
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vulnscan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Security: Rate Limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

def validate_target(target):
    """Validasi IP atau Domain untuk mencegah input berbahaya."""
    ip_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    domain_regex = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$"
    return re.match(ip_regex, target) or re.match(domain_regex, target) or target == "localhost"

def background_scan(app_context, target_id, scan_id, target_host, start_port, end_port):
    """Fungsi yang berjalan di thread terpisah untuk proses scanning."""
    with app_context:
        scanner = ScannerCore(target_host, start_port, end_port)
        results = scanner.run_scan()
        
        # Update database setelah scan selesai
        scan_record = ScanHistory.query.get(scan_id)
        scan_record.status = 'Completed' if results else 'Failed (Unreachable)'
        scan_record.total_open_ports = len(results)
        
        for res in results:
            new_port = PortDetails(
                scan_id=scan_id,
                port=res['port'],
                state=res['state'],
                service=res['service'],
                banner=res['banner'],
                http_server=res['http_server'],
                http_status=res['http_status']
            )
            db.session.add(new_port)
            
        db.session.commit()

@app.route('/')
def dashboard():
    total_scans = ScanHistory.query.count()
    completed_scans = ScanHistory.query.filter_by(status='Completed').count()
    total_ports = PortDetails.query.count()
    recent_scans = ScanHistory.query.order_by(ScanHistory.id.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           total_scans=total_scans, 
                           completed_scans=completed_scans, 
                           total_ports=total_ports,
                           recent_scans=recent_scans)

@app.route('/scan', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def new_scan():
    if request.method == 'POST':
        target_host = request.form.get('target').strip()
        start_port = int(request.form.get('start_port', 1))
        end_port = int(request.form.get('end_port', 1024))
        
        if not validate_target(target_host):
            return "Invalid target format. Use IP or Domain.", 400
            
        # Simpan ke DB Target
        target_record = ScanTarget.query.filter_by(target=target_host).first()
        if not target_record:
            target_record = ScanTarget(target=target_host)
            db.session.add(target_record)
            db.session.commit()
            
        # Buat record Scan History
        new_scan_record = ScanHistory(target_id=target_record.id, status='Running')
        db.session.add(new_scan_record)
        db.session.commit()
        
        # Jalankan thread
        thread = threading.Thread(
            target=background_scan, 
            args=(app.app_context(), target_record.id, new_scan_record.id, target_host, start_port, end_port)
        )
        thread.start()
        
        return redirect(f'/scan/{new_scan_record.id}')
        
    return render_template('scan.html')

@app.route('/scan/<int:scan_id>')
def scan_details(scan_id):
    scan_record = ScanHistory.query.get_or_404(scan_id)
    ports = PortDetails.query.filter_by(scan_id=scan_id).all()
    return render_template('scan_detail.html', scan=scan_record, ports=ports)

@app.route('/api/status/<int:scan_id>')
def api_status(scan_id):
    """Endpoint AJAX untuk mengecek status realtime."""
    scan_record = ScanHistory.query.get(scan_id)
    if not scan_record:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "status": scan_record.status,
        "ports_found": scan_record.total_open_ports
    })

@app.route('/history')
def history():
    scans = ScanHistory.query.order_by(ScanHistory.scan_time.desc()).all()
    return render_template('history.html', scans=scans)

@app.route('/export/csv/<int:scan_id>')
def export_csv(scan_id):
    scan_record = ScanHistory.query.get_or_404(scan_id)
    ports = PortDetails.query.filter_by(scan_id=scan_id).all()
    csv_data = generate_csv(ports, scan_record.target_info.target)
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=scan_{scan_id}.csv"}
    )

@app.route('/export/pdf/<int:scan_id>')
def export_pdf(scan_id):
    scan_record = ScanHistory.query.get_or_404(scan_id)
    ports = PortDetails.query.filter_by(scan_id=scan_id).all()
    pdf_data = generate_pdf(scan_record, ports)
    
    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'scan_{scan_id}.pdf'
    )

@app.route('/api/delete/<int:scan_id>', methods=['POST'])
def delete_scan(scan_id):
    try:
        # Menggunakan db.session.get() yang sepenuhnya didukung oleh Flask-SQLAlchemy 3.x+
        scan = db.session.get(ScanHistory, scan_id)
        
        # Fallback jika menggunakan struktur query lama
        if not scan:
            scan = ScanHistory.query.filter_by(id=scan_id).first()
            
        if scan:
            # 1. Hapus semua detail port yang terhubung dengan scan_id ini terlebih dahulu
            PortDetails.query.filter_by(scan_id=scan_id).delete()
            
            # 2. Hapus data riwayat scan utama
            db.session.delete(scan)
            
            # 3. Commit transaksi ke database SQLite
            db.session.commit()
            return jsonify({"success": True, "message": "Scan history deleted successfully."})
            
        return jsonify({"success": False, "message": "Scan not found."}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, threaded=True)