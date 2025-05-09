import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from nltk.tokenize import word_tokenize
import nltk
import re

def preprocess_text(text):
    """Clean and tokenize text."""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Tokenize
    return word_tokenize(text)

def train_word2vec_model(courses_df):
    """Train a Word2Vec model on course descriptions."""
    # Download required NLTK data
    nltk.download('punkt')
    
    # Prepare sentences for training
    sentences = []
    for _, row in courses_df.iterrows():
        # Combine title and description for better context
        text = f"{row['title']} {row['description']}"
        tokens = preprocess_text(text)
        sentences.append(tokens)
    
    # Train Word2Vec model
    model = Word2Vec(sentences=sentences, vector_size=100, window=5, min_count=1, workers=4)
    return model

def get_document_embedding(text, model):
    """Get embedding for a document by averaging word vectors."""
    tokens = preprocess_text(text)
    vectors = []
    
    for token in tokens:
        if token in model.wv:
            vectors.append(model.wv[token])
    
    if vectors:
        return np.mean(vectors, axis=0)
    return np.zeros(model.vector_size)

def generate_course_embeddings(input_files):
    """Generate embeddings for all courses."""
    # Load and combine course data
    dfs = []
    for file in input_files:
        df = pd.read_csv(file)
        dfs.append(df)
    courses_df = pd.concat(dfs, ignore_index=True)
    
    # Train Word2Vec model
    model = train_word2vec_model(courses_df)
    
    # Generate embeddings for each course
    embeddings = {}
    for _, row in courses_df.iterrows():
        # Combine title and description for embedding
        text = f"{row['title']} {row['description']}"
        embedding = get_document_embedding(text, model)
        
        # Create a unique key for the course
        course_key = f"{row['institution']}_{row['course_code']}"
        embeddings[course_key] = embedding.tolist()
    
    return embeddings

if __name__ == "__main__":
    input_files = ['sample_courses.csv', 'csusb_courses.csv']
    embeddings = generate_course_embeddings(input_files)
    print(f"Generated embeddings for {len(embeddings)} courses") 