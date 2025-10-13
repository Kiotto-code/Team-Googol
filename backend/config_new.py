#!/usr/bin/env python3
"""
Configuration module for FINDR system.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'findr_new.db'
    ))
    
    # Upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads'
    ))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CORS configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'findr:'
    SESSION_COOKIE_NAME = 'findr_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_SECURE', 'False').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # API configuration
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '1000 per hour')
    API_VERSION = '2.0'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'findr.log')
    
    # CLIP/AI configuration
    CLIP_MODEL_NAME = os.environ.get('CLIP_MODEL_NAME', 'ViT-B/32')
    DEVICE = os.environ.get('DEVICE', 'auto')  # 'cpu', 'cuda', or 'auto'
    
    # Box/Hardware configuration
    DEFAULT_BOX_LOCATIONS = [
        'Library - Level 1',
        'Library - Level 2', 
        'Student Center',
        'Engineering Building',
        'Science Building',
        'Arts Building'
    ]
    
    # Cleanup configuration
    CLEANUP_INTERVAL_HOURS = int(os.environ.get('CLEANUP_INTERVAL_HOURS', 24))
    KEEP_FILES_DAYS = int(os.environ.get('KEEP_FILES_DAYS', 30))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'findr_dev.db')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests
    SECRET_KEY = 'test-secret-key'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])