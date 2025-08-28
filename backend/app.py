from flask import Flask
from flask_cors import CORS
from routes.upload import upload_bp
from routes.search import search_bp
from routes.delete import delete_bp
from routes.claim import claim_bp
from routes.collect import collect_bp
from flask import send_from_directory
from clip_utils import UPLOAD_FOLDER
from scheduler import start_cleanup_scheduler
import atexit

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Register routes
app.register_blueprint(upload_bp)
app.register_blueprint(search_bp)
app.register_blueprint(delete_bp)
app.register_blueprint(claim_bp)
app.register_blueprint(collect_bp)

# Start the cleanup scheduler
start_cleanup_scheduler()

# Ensure cleanup scheduler stops when the app shuts down
atexit.register(lambda: __import__('scheduler').stop_cleanup_scheduler())

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
