"""
Centralized error handling and logging utilities.
"""
import logging
import traceback
from functools import wraps
from flask import jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base application error class."""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message):
        super().__init__(message, status_code=400)

class NotFoundError(AppError):
    """Not found error."""
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)

def handle_errors(f):
    """Decorator for consistent error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            logger.warning(f"Application error: {e.message}")
            response = {"error": e.message}
            if e.payload:
                response.update(e.payload)
            return jsonify(response), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "Internal server error"}), 500
    return decorated_function

def log_request(f):
    """Decorator for logging API requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        logger.info(f"API Request: {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function
