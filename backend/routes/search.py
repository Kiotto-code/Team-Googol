import os
import numpy as np
from flask import Blueprint, request, jsonify, send_file
from clip_utils import get_text_embedding, image_data, UPLOAD_FOLDER

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search_image():
    data = request.get_json()
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    query = data['query']

    text_emb = get_text_embedding(query).cpu().numpy()
    best_score, best_image = -1, None

    for fname, emb in image_data.items():
        img_emb = np.array(emb)
        score = np.dot(text_emb, img_emb.T).item()
        if score > best_score:
            best_score, best_image = score, fname

    if best_image and best_score >= 0.2:
        return send_file(os.path.join(UPLOAD_FOLDER, best_image), mimetype='image/jpeg')
    else:
        return jsonify({"error": "No matching image found", "best_score": float(best_score)}), 404