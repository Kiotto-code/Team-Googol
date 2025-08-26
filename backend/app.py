from flask import Flask
from flask_cors import CORS
from routes.upload import upload_bp
from routes.search import search_bp
from routes.delete import delete_bp
from flask import send_from_directory
from clip_utils import UPLOAD_FOLDER

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Register routes
app.register_blueprint(upload_bp)
app.register_blueprint(search_bp)
app.register_blueprint(delete_bp)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
