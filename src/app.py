from flask import Flask, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from routes.tbr import tbr
import os
import logging

# Get absolute paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, 'static')
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__,
            static_folder=static_dir,
            template_folder=template_dir)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Add a secret key for CSRF
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure value
csrf = CSRFProtect(app)

# Register blueprints with explicit url_prefix
app.register_blueprint(tbr, url_prefix='/tbr')

@app.route('/')
def index():
    return redirect(url_for('tbr.manager'))

if __name__ == '__main__':
    app.logger.info(f"Static folder: {app.static_folder}")
    app.logger.info(f"Template folder: {app.template_folder}")
    app.logger.info(f"Template exists: {os.path.exists(os.path.join(template_dir, 'tbr', 'tbr_manager.html'))}")
    app.run(debug=True)
