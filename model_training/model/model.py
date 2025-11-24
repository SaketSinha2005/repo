import numpy as np
import pickle
import os
import re
from tensorflow import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences


class SpamClassifier:
    def __init__(self, model_path=None, tokenizer_path=None, max_length=100):
        self.max_length = max_length
        
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), 
                'saved_models', 
                'spam_classifier.h5'
            )
        
        if tokenizer_path is None:
            tokenizer_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'data', 
                'tokenizer.pkl'
            )
        
        print(f"Loading model from: {model_path}")
        self.model = keras.models.load_model(model_path)
        print(f"Loading tokenizer from: {tokenizer_path}")
        with open(tokenizer_path, 'rb') as f:
            self.tokenizer = pickle.load(f)
        
        print("Spam classifier initialized successfully!")
    
    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\b\d{10,}\b', '', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        text = re.sub(r'[^a-z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def preprocess(self, text):
        cleaned = self.clean_text(text)
        sequence = self.tokenizer.texts_to_sequences([cleaned])
        
        padded = pad_sequences(
            sequence, 
            maxlen=self.max_length, 
            padding='post', 
            truncating='post'
        )
        
        return padded
    
    def predict(self, text):
        input_data = self.preprocess(text)
        
        # Predict
        probability = self.model.predict(input_data, verbose=0)[0][0]
        
        # Determine class (threshold = 0.5)
        is_spam = probability > 0.5
        
        return {
            'prediction': 'spam' if is_spam else 'ham',
            'confidence': float(probability if is_spam else 1 - probability),
            'spam_probability': float(probability)
        }
    
    def predict_batch(self, texts):
        results = []
        
        for text in texts:
            results.append(self.predict(text))
        
        return results


# Example usage
if __name__ == "__main__":
    # Test the classifier
    classifier = SpamClassifier()
    
    # Test cases
    test_emails = [
        "FREE MONEY! Click here to win $1000 now! Call 1-800-WINNER",
        "Hi, I would like to return my damaged product. Can you help?",
        "Congratulations! You've won a FREE iPhone! Text YES to claim",
        "Meeting scheduled for tomorrow at 3pm. See you there.",
        "URGENT! Your account will be closed unless you verify now!"
    ]
    
    print("\n" + "="*70)
    print("Testing Spam Classifier")
    print("="*70)
    
    for email in test_emails:
        result = classifier.predict(email)
        print(f"\nEmail: {email[:60]}...")
        print(f"Prediction: {result['prediction'].upper()}")
        print(f"Confidence: {result['confidence']:.2%}")
        print("-"*70)
