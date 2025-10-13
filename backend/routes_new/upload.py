#!/usr/bin/env python3
"""
File upload routes for FINDR system.
"""

from flask import Blueprint, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import logging

upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename while preserving extension."""
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        return f"{uuid.uuid4().hex}.{ext.lower()}"
    else:
        return f"{uuid.uuid4().hex}"

@upload_bp.route('/image', methods=['POST'])
def upload_image():
    """Upload an image file."""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'status': 'error',
                'message': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Check if file extension is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create file URL (relative to the backend)
        file_url = f'/uploads/{unique_filename}'
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'data': {
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_url': file_url,
                'file_size': file_size,
                'file_path': file_path
            }
        })
    
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to upload image',
            'error': str(e)
        }), 500

@upload_bp.route('/multiple', methods=['POST'])
def upload_multiple_images():
    """Upload multiple image files."""
    try:
        # Check if files are in request
        if 'files' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No files provided'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or (len(files) == 1 and files[0].filename == ''):
            return jsonify({
                'status': 'error',
                'message': 'No files selected'
            }), 400
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    errors.append({
                        'filename': file.filename,
                        'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
                    })
                    continue
                
                # Check if file extension is allowed
                if not allowed_file(file.filename):
                    errors.append({
                        'filename': file.filename,
                        'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                    })
                    continue
                
                # Generate unique filename
                original_filename = secure_filename(file.filename)
                unique_filename = generate_unique_filename(original_filename)
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Create file URL
                file_url = f'/uploads/{unique_filename}'
                
                uploaded_files.append({
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_url': file_url,
                    'file_size': file_size,
                    'file_path': file_path
                })
                
            except Exception as file_error:
                errors.append({
                    'filename': file.filename,
                    'error': str(file_error)
                })
        
        return jsonify({
            'status': 'success' if uploaded_files else 'error',
            'message': f'Uploaded {len(uploaded_files)} files successfully',
            'data': {
                'uploaded_files': uploaded_files,
                'errors': errors,
                'uploaded_count': len(uploaded_files),
                'error_count': len(errors)
            }
        })
    
    except Exception as e:
        logger.error(f"Error uploading multiple images: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to upload images',
            'error': str(e)
        }), 500

@upload_bp.route('/info/<filename>', methods=['GET'])
def get_file_info(filename):
    """Get information about an uploaded file."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        file_stats = os.stat(file_path)
        file_url = f'/uploads/{filename}'
        
        return jsonify({
            'status': 'success',
            'data': {
                'filename': filename,
                'file_url': file_url,
                'file_size': file_stats.st_size,
                'created_at': file_stats.st_ctime,
                'modified_at': file_stats.st_mtime,
                'file_path': file_path
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting file info for {filename}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get file information',
            'error': str(e)
        }), 500

@upload_bp.route('/list', methods=['GET'])
def list_uploaded_files():
    """List all uploaded files."""
    try:
        files = []
        
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            if os.path.isfile(file_path):
                file_stats = os.stat(file_path)
                file_url = f'/uploads/{filename}'
                
                files.append({
                    'filename': filename,
                    'file_url': file_url,
                    'file_size': file_stats.st_size,
                    'created_at': file_stats.st_ctime,
                    'modified_at': file_stats.st_mtime
                })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': files,
            'count': len(files)
        })
    
    except Exception as e:
        logger.error(f"Error listing uploaded files: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to list uploaded files',
            'error': str(e)
        }), 500

@upload_bp.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete an uploaded file."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'message': 'File deleted successfully',
            'filename': filename
        })
    
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete file',
            'error': str(e)
        }), 500

@upload_bp.route('/stats', methods=['GET'])
def get_upload_stats():
    """Get upload statistics."""
    try:
        files = os.listdir(UPLOAD_FOLDER)
        file_count = len([f for f in files if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
        
        total_size = 0
        for filename in files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'upload_folder': UPLOAD_FOLDER,
                'allowed_extensions': list(ALLOWED_EXTENSIONS),
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024)
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting upload stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get upload statistics',
            'error': str(e)
        }), 500