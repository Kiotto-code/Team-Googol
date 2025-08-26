import os
import numpy as np
from flask import Blueprint, request, jsonify, send_file
from clip_utils import get_text_embedding, UPLOAD_FOLDER
from database import search_items, release_expired_claims

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search_image():
    data = request.get_json()
    if 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data['query']
    
    # Clean up expired claims before searching
    release_expired_claims()

    # Move tensor to CPU and convert to NumPy
    query_emb = get_text_embedding(query).detach().cpu().numpy().flatten().tolist()

    # Search in database
    results = search_items(query_emb, threshold=0.2)
        
    if not results:
        return jsonify({"message": "Image not found"}), 404

    # Sort by similarity descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Add URLs to results
    for r in results:
        r["url"] = f"http://127.0.0.1:5000/uploads/{r['filename']}"
        # Add claim status information for frontend
        r["can_claim"] = r["status"] == "available"
        r["is_claimed"] = r["status"] == "claimed"

    return jsonify({"results": results})
