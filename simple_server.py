#!/usr/bin/env python3
"""
Simplified Flask application for testing the new FINDR system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import logging

# Import database functions
from database_new import init_database, get_system_stats

# Import route blueprints one by one to isolate issues
try:
    from routes_new.auth import auth_bp
    print("✅ Auth routes imported")
except Exception as e:
    print(f"❌ Auth routes failed: {e}")
    auth_bp = None

try:
    from routes_new.users import users_bp
    print("✅ Users routes imported")
except Exception as e:
    print(f"❌ Users routes failed: {e}")
    users_bp = None

try:
    from routes_new.items import items_bp
    print("✅ Items routes imported")
except Exception as e:
    print(f"❌ Items routes failed: {e}")
    items_bp = None

try:
    from routes_new.boxes import boxes_bp
    print("✅ Boxes routes imported")
except Exception as e:
    print(f"❌ Boxes routes failed: {e}")
    boxes_bp = None

try:
    from routes_new.cases import cases_bp
    print("✅ Cases routes imported")
except Exception as e:
    print(f"❌ Cases routes failed: {e}")
    cases_bp = None

try:
    from routes_new.search import search_bp
    print("✅ Search routes imported")
except Exception as e:
    print(f"❌ Search routes failed: {e}")
    search_bp = None

try:
    from routes_new.upload import upload_bp
    print("✅ Upload routes imported")
except Exception as e:
    print(f"❌ Upload routes failed: {e}")
    upload_bp = None

app = Flask(__name__)
app.secret_key = 'dev-secret-key-for-testing'

# Configure CORS
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints if they imported successfully
if auth_bp:
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    print("✅ Auth blueprint registered")

if users_bp:
    app.register_blueprint(users_bp, url_prefix='/api/users')
    print("✅ Users blueprint registered")

if items_bp:
    app.register_blueprint(items_bp, url_prefix='/api/items')
    print("✅ Items blueprint registered")

if boxes_bp:
    app.register_blueprint(boxes_bp, url_prefix='/api/boxes')
    print("✅ Boxes blueprint registered")

if cases_bp:
    app.register_blueprint(cases_bp, url_prefix='/api/cases')
    print("✅ Cases blueprint registered")

if search_bp:
    app.register_blueprint(search_bp, url_prefix='/api/search')
    print("✅ Search blueprint registered")

if upload_bp:
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    print("✅ Upload blueprint registered")

@app.route('/')
def home():
    """Home endpoint with system info."""
    return jsonify({
        'status': 'success',
        'message': 'FINDR API Server is running',
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'auth': '/api/auth' if auth_bp else 'disabled',
            'users': '/api/users' if users_bp else 'disabled',
            'items': '/api/items' if items_bp else 'disabled',
            'boxes': '/api/boxes' if boxes_bp else 'disabled',
            'cases': '/api/cases' if cases_bp else 'disabled',
            'search': '/api/search' if search_bp else 'disabled',
            'upload': '/api/upload' if upload_bp else 'disabled'
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        stats = get_system_stats()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/stats')
def system_stats():
    """Get system statistics."""
    try:
        stats = get_system_stats()
        return jsonify({
            'status': 'success',
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'error_code': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error_code': 500
    }), 500

if __name__ == '__main__':
    print("🔧 Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    port = 5002
    logger.info(f"Starting FINDR server on port {port}")
    
    print(f"🚀 Starting FINDR server on http://127.0.0.1:{port}")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=True,
        threaded=True
    )