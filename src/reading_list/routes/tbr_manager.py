from flask import Blueprint, render_template
from flask_wtf.csrf import generate_csrf

tbr_bp = Blueprint('tbr', __name__, url_prefix='/tbr')

@tbr_bp.route('/')
def index():
    csrf_token = generate_csrf()
    return render_template('tbr/tbr_manager.html', csrf_token=csrf_token)
