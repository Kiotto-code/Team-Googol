# routes.py

from flask import Blueprint, render_template

# Create the blueprint
page_bp = Blueprint("page_bp", __name__, template_folder="frontend")

# Routes
@page_bp.route("/home")
def home():
    return render_template("index.html")

@page_bp.route("/admin")
def admin():
    return render_template("admin.html")

@page_bp.route("/found")
def found():
    return render_template("found.html")
