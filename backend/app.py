#!/usr/bin/env python3
"""
Main Flask application for FINDR system with new database schema.
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime

# Import the database module
from database import init_database, get_system_stats

# Import route modules
from routes.users import users_bp
from routes.items import items_bp
from routes.boxes import boxes_bp
from routes.cases import cases_bp
from routes.upload import upload_bp
from routes.search import search_bp
from routes.auth import auth_bp

app = Flask(__name__)

# Configure Flask
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure CORS
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(items_bp, url_prefix='/api/items')
app.register_blueprint(boxes_bp, url_prefix='/api/boxes')
app.register_blueprint(cases_bp, url_prefix='/api/cases')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(search_bp, url_prefix='/api/search')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.route('/')
def home():
    """Home endpoint with system info."""
    return jsonify({
        'status': 'success',
        'message': 'FINDR API Server is running',
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'auth': '/api/auth',
            'users': '/api/users',
            'items': '/api/items',
            'boxes': '/api/boxes',
            'cases': '/api/cases',
            'upload': '/api/upload',
            'search': '/api/search'
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

# Frontend static file serving
@app.route('/frontend')
def frontend():
    """Serve the main frontend page."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/frontend/<path:filename>')
def frontend_files(filename):
    """Serve frontend static files."""
    return send_from_directory('../frontend', filename)

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

# Remove deprecated before_first_request - we'll initialize in main instead

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Start the server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting FINDR server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )