from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.model import SpamClassifier

app = Flask(__name__)
CORS(app)  

try:
    classifier = SpamClassifier()
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    classifier = None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model_loaded': classifier is not None})

@app.route('/predict', methods=['POST'])
def predict():
    if not classifier:
        return jsonify({'error': 'Model not loaded'}), 500

    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    
    try:
        result = classifier.predict(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
