import pandas as pd
import numpy as np
import re
import pickle
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os


# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
TRAIN_CSV = os.path.join(DATA_DIR, 'train.csv')
PREPROCESSED_TRAIN = os.path.join(DATA_DIR, 'preprocessed_train.csv')
PREPROCESSED_TEST = os.path.join(DATA_DIR, 'preprocessed_test.csv')
TOKENIZER_PATH = os.path.join(DATA_DIR, 'tokenizer.pkl')

MAX_WORDS = 10000  
MAX_SEQUENCE_LENGTH = 100  
TEST_SIZE = 0.2
RANDOM_STATE = 42


def clean_text(text):
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


def load_and_clean_data(filepath):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    print(f"Original data shape: {df.shape}")
    print(f"\nClass distribution:\n{df['Category'].value_counts()}")
    
    # Filter out invalid categories (keep only 'ham' and 'spam')
    valid_categories = df['Category'].isin(['ham', 'spam'])
    invalid_count = (~valid_categories).sum()
    if invalid_count > 0:
        print(f"\nWarning: Found {invalid_count} rows with invalid categories. Removing them...")
        df = df[valid_categories]
    
    print("\nCleaning text...")
    df['cleaned_message'] = df['Message'].apply(clean_text)
    
    df = df[df['cleaned_message'].str.len() > 0]
    
    df['label'] = df['Category'].map({'ham': 0, 'spam': 1})
    
    print(f"Data shape after cleaning: {df.shape}")
    
    return df


def create_tokenizer(texts, max_words=MAX_WORDS):
    print(f"\nCreating tokenizer with max_words={max_words}...")
    tokenizer = Tokenizer(num_words=max_words, oov_token='<OOV>')
    tokenizer.fit_on_texts(texts)
    
    print(f"Vocabulary size: {len(tokenizer.word_index)}")
    
    return tokenizer


def preprocess_texts(tokenizer, texts, max_length=MAX_SEQUENCE_LENGTH):
    
    sequences = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(sequences, maxlen=max_length, padding='post', truncating='post')
    
    return padded


def save_tokenizer(tokenizer, filepath):
    """Save tokenizer to pickle file."""
    print(f"\nSaving tokenizer to {filepath}...")
    with open(filepath, 'wb') as f:
        pickle.dump(tokenizer, f)
    print("Tokenizer saved successfully!")


def preprocess_dataset():
    df = load_and_clean_data(TRAIN_CSV)
    
    tokenizer = create_tokenizer(df['cleaned_message'].values, MAX_WORDS)
    
    print(f"\nSplitting data (test_size={TEST_SIZE})...")
    train_df, test_df = train_test_split(
        df, 
        test_size=TEST_SIZE, 
        random_state=RANDOM_STATE,
        stratify=df['label']
    )
    
    print(f"Train size: {len(train_df)}")
    print(f"Test size: {len(test_df)}")
    
    print("\nConverting texts to sequences...")
    train_sequences = preprocess_texts(tokenizer, train_df['cleaned_message'].values, MAX_SEQUENCE_LENGTH)
    test_sequences = preprocess_texts(tokenizer, test_df['cleaned_message'].values, MAX_SEQUENCE_LENGTH)
    
    train_df['sequence'] = list(train_sequences)
    test_df['sequence'] = list(test_sequences)
    
    print(f"\nSaving preprocessed data...")
    train_df.to_csv(PREPROCESSED_TRAIN, index=False)
    test_df.to_csv(PREPROCESSED_TEST, index=False)
    print(f"Train data saved to: {PREPROCESSED_TRAIN}")
    print(f"Test data saved to: {PREPROCESSED_TEST}")
    
    save_tokenizer(tokenizer, TOKENIZER_PATH)
    
    print("\n" + "="*50)
    print("Preprocessing completed successfully!")
    print("="*50)
    print(f"\nNext steps:")
    print(f"1. Open model_training/notebookLM/model.ipynb")
    print(f"2. Train the CNN model")
    print(f"3. Evaluate and save the model")


if __name__ == "__main__":
    preprocess_dataset()
