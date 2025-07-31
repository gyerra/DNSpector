from flask import Flask, render_template, jsonify, request, send_file
import json
from datetime import datetime, timedelta
from db import DNSDatabase
import os

app = Flask(__name__)
db = DNSDatabase()

@app.route('/')
def index():
    """Main dashboard page"""
    domains = db.get_all_domains()
    resolvers = db.get_all_resolvers()
    recent_alerts = db.get_recent_alerts(limit=10)
    
    return render_template('dashboard.html', 
                         domains=domains, 
                         resolvers=resolvers,
                         recent_alerts=recent_alerts)

@app.route('/api/data/<domain>')
def get_domain_data(domain):
    """API endpoint to get domain history data"""
    resolver = request.args.get('resolver')
    limit = int(request.args.get('limit', 100))
    
    data = db.get_domain_history(domain, resolver, limit)
    
    # Format data for Chart.js
    chart_data = {
        'labels': [],
        'ips': [],
        'ttls': [],
        'latencies': [],
        'resolvers': []
    }
    
    for entry in reversed(data):  # Reverse to show chronological order
        chart_data['labels'].append(entry['timestamp'])
        chart_data['ips'].append(entry['ip'] or 'N/A')
        chart_data['ttls'].append(entry['ttl'] or 0)
        chart_data['latencies'].append(entry['latency_ms'])
        chart_data['resolvers'].append(entry['resolver'])
    
    return jsonify(chart_data)

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get recent alerts"""
    limit = int(request.args.get('limit', 50))
    alerts = db.get_recent_alerts(limit)
    return jsonify(alerts)

@app.route('/api/domains')
def get_domains():
    """API endpoint to get all domains"""
    domains = db.get_all_domains()
    return jsonify(domains)

@app.route('/api/resolvers')
def get_resolvers():
    """API endpoint to get all resolvers"""
    resolvers = db.get_all_resolvers()
    return jsonify(resolvers)

@app.route('/export/csv')
def export_csv():
    """Export DNS logs to CSV"""
    domain = request.args.get('domain')
    resolver = request.args.get('resolver')
    
    filename = f'dns_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = os.path.join('logs', filename)
    
    db.export_to_csv(filepath, domain, resolver)
    
    return send_file(filepath, 
                    as_attachment=True, 
                    download_name=filename,
                    mimetype='text/csv')

@app.route('/export/json')
def export_json():
    """Export DNS logs to JSON"""
    domain = request.args.get('domain')
    resolver = request.args.get('resolver')
    
    filename = f'dns_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    filepath = os.path.join('logs', filename)
    
    db.export_to_json(filepath, domain, resolver)
    
    return send_file(filepath, 
                    as_attachment=True, 
                    download_name=filename,
                    mimetype='application/json')

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000) 