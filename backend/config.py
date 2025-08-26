"""
Configuration settings for the Lost & Found application.
"""
import os

class Config:
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'lost_and_found.db')
    
    # File uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
    
    # CLIP model
    CLIP_MODEL = os.getenv('CLIP_MODEL', 'ViT-L/14@336px')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://127.0.0.1:5500').split(',')
    
    # Claims
    CLAIM_DURATION_HOURS = int(os.getenv('CLAIM_DURATION_HOURS', 1))
    
    # Search
    DEFAULT_SEARCH_THRESHOLD = float(os.getenv('DEFAULT_SEARCH_THRESHOLD', 0.2))

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_PATH = 'dev_lost_and_found.db'

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")

# Config selection
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
