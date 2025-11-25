import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_training.model.model import SpamClassifier
from src.workflow import process_email

load_dotenv()

app = Flask(__name__)
CORS(app)  

try:
    spam_classifier = SpamClassifier()
    print("Spam classifier loaded successfully")
except Exception as e:
    print(f"Error loading spam classifier: {e}")
    spam_classifier = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "spam_classifier": spam_classifier is not None,
        "version": "1.0.0"
    })


@app.route('/classify-email', methods=['POST'])
def classify_email():
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({"error": "Missing 'email' in request body"}), 400
        
        email_text = data['email']
        
        if not spam_classifier:
            return jsonify({"error": "Spam classifier not initialized"}), 500
        
        # Classify email
        result = spam_classifier.predict(email_text)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate-response', methods=['POST'])
def generate_response():
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({"error": "Missing 'email' in request body"}), 400
        
        email_text = data['email']
        
        # Step 1: Check if spam
        if spam_classifier:
            spam_result = spam_classifier.predict(email_text)
            
            if spam_result['prediction'] == 'spam':
                return jsonify({
                    "is_spam": True,
                    "spam_confidence": spam_result['confidence'],
                    "response": None,
                    "message": "Email classified as spam. No response generated.",
                    "success": True
                })
        else:
            spam_result = {"prediction": "ham", "confidence": 0.5}
        
        print(f"Generating response for email: {email_text[:100]}...")
        result = process_email(email_text)
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error during response generation')
            print(f"Response generation failed: {error_msg}")
            return jsonify({
                "is_spam": False,
                "spam_confidence": 1 - spam_result.get('spam_probability', 0.5),
                "response": None,
                "success": False,
                "error": error_msg
            }), 500
        
        print(f"Response generated successfully")
        return jsonify({
            "is_spam": False,
            "spam_confidence": 1 - spam_result.get('spam_probability', 0.5),
            "response": result.get('response'),
            "classification": result.get('classification'),
            "validation": result.get('validation'),
            "success": True
        })
    
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"Server error: {error_msg}")
        return jsonify({
            "is_spam": False,
            "response": None,
            "success": False,
            "error": error_msg
        }), 500


@app.route('/test', methods=['GET'])
def test_endpoint():
    sample_email = "I would like to return my laptop that I purchased last week. It has a screen issue."
    
    result = process_email(sample_email)
    
    return jsonify({
        "test_email": sample_email,
        "result": result
    })


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print("\n" + "="*70)
    print("Gmail Customer Service Backend Server")
    print("="*70)
    print(f"Server running on: http://localhost:{port}")
    print(f"Swagger docs: http://localhost:{port}/test")
    print(f"Debug mode: {debug}")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
