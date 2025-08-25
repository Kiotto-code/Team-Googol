import os
import torch
import clip
from PIL import Image
import numpy as np
from flask_cors import CORS
from flask import Flask, request, jsonify, send_file
import json
from werkzeug.utils import secure_filename

# Initialize Flask and CLIP
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14@336px", device=device)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# File to store embeddings metadata
DATA_FILE = "data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        image_data = json.load(f)
else:
    image_data = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(image_data, f)

# Compute image embedding
def get_image_embedding(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image)
    return embedding / embedding.norm(dim=-1, keepdim=True)

# Compute text embedding
def get_text_embedding(text):
    text_tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        embedding = model.encode_text(text_tokens)
    return embedding / embedding.norm(dim=-1, keepdim=True)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Compute and store image embedding
    embedding = get_image_embedding(filepath).cpu().numpy().tolist()
    image_data[filename] = embedding
    save_data()

    return jsonify({"message": "Image uploaded successfully", "filename": filename})

@app.route('/search', methods=['POST'])
def search_image():
    data = request.get_json()
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    query = data['query']
    
    text_embedding = get_text_embedding(query).cpu().numpy()
    best_score = -1
    best_image = None

    # Compute cosine similarity with stored embeddings
    for fname, emb in image_data.items():
        img_emb = np.array(emb)
        score = np.dot(text_embedding, img_emb.T).item()  # Cosine similarity
        if score > best_score:
            best_score = score
            best_image = fname

    if best_image:
        return send_file(os.path.join(UPLOAD_FOLDER, best_image), mimetype='image/jpeg')
    else:
        return jsonify({"error": "No matching image found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
