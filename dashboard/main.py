from flask import Flask, render_template
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# API configuration
API_URL = os.getenv('API_URL', 'https://api-demo-joinsdemo-prod.demo.quix.io/api/data')

@app.route('/')
def index():
    return render_template('index.html', api_url=API_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
