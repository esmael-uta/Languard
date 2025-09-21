# app_amplify.py - Simplified version for AWS Amplify
import os
from flask import Flask, render_template

app = Flask(__name__)

# Basic configuration
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Main route
@app.route('/')
def index():
    return render_template('index.html')

# Health check route (important for Amplify)
@app.route('/health')
def health():
    return 'OK', 200

# Catch all other routes and serve index.html
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)