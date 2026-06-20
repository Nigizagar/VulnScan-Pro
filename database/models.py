from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ScanTarget(db.Model):
    __tablename__ = 'targets'
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scans = db.relationship('ScanHistory', backref='target_info', lazy=True)

class ScanHistory(db.Model):
    __tablename__ = 'scans'
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    status = db.Column(db.String(20), default='Running') # Running, Completed, Failed
    scan_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_open_ports = db.Column(db.Integer, default=0)
    ports = db.relationship('PortDetails', backref='scan_info', lazy=True)

class PortDetails(db.Model):
    __tablename__ = 'ports'
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    state = db.Column(db.String(20), default='Open')
    service = db.Column(db.String(50), nullable=True)
    banner = db.Column(db.Text, nullable=True)
    http_server = db.Column(db.String(100), nullable=True)
    http_status = db.Column(db.String(10), nullable=True)