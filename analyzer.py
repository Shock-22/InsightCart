import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from typing import Dict, List, Union

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Initialize BERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
model = AutoModel.from_pretrained('bert-base-uncased')

def get_bert_embeddings(text: str) -> np.ndarray:
    """Get BERT embeddings for a given text."""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment of text using VADER."""
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)

def calculate_review_score(review: Dict) -> float:
    """Calculate a score for a single review based on sentiment and rating."""
    # Get sentiment scores
    content = review.get('content', '')
    sentiment = analyze_sentiment(content)
    
    # Convert rating to float (assuming 5-star scale)
    try:
        rating = float(review.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0
    
    # Normalize rating to 0-1 scale
    normalized_rating = rating / 5.0 if rating > 0 else 0
    
    # Calculate weighted score (sentiment compound + normalized rating)
    sentiment_weight = 0.4
    rating_weight = 0.6
    
    sentiment_score = (sentiment['compound'] + 1) / 2  # Convert from [-1,1] to [0,1]
    weighted_score = (sentiment_score * sentiment_weight) + (normalized_rating * rating_weight)
    
    return weighted_score * 100  # Convert to 0-100 scale

def calculate_rating_score(rating_distribution: Dict[str, float]) -> float:
    """Calculate a score based on rating distribution."""
    if not rating_distribution or sum(rating_distribution.values()) == 0:
        return 0
    
    # Calculate weighted average
    total_weight = sum(rating_distribution.values())
    weighted_sum = sum(float(stars) * percentage 
                      for stars, percentage in rating_distribution.items())
    
    # Normalize to 0-100 scale
    return (weighted_sum / total_weight) * 20  # Convert 5-star scale to 100-point scale

def analyze_features(specifications: Dict[str, Union[str, List[str]]]) -> float:
    """Analyze product features using BERT embeddings."""
    if not specifications:
        return 50  # Neutral score if no features available
    
    # Convert specifications to text
    feature_text = ' '.join(str(v) for v in specifications.values())
    
    # Get sentiment of features
    feature_sentiment = analyze_sentiment(feature_text)
    
    # Convert sentiment to score (0-100)
    feature_score = ((feature_sentiment['compound'] + 1) / 2) * 100
    
    return feature_score

def calculate_metacritic_score(product_data: Dict) -> Dict[str, Union[float, Dict[str, float]]]:
    """Calculate overall metacritic score and component scores."""
    # Initialize scores
    review_scores = []
    rating_score = 0
    feature_score = 50  # Default neutral score
    
    # Calculate review scores
    if product_data.get('reviews'):
        review_scores = [calculate_review_score(review) for review in product_data['reviews']]
    
    # Calculate rating distribution score
    if product_data.get('rating_distribution'):
        rating_score = calculate_rating_score(product_data['rating_distribution'])
    
    # Calculate feature score
    if product_data.get('specifications'):
        feature_score = analyze_features(product_data['specifications'])
    
    # Calculate final weighted score
    weights = {
        'reviews': 0.4,
        'ratings': 0.4,
        'features': 0.2
    }
    
    avg_review_score = sum(review_scores) / len(review_scores) if review_scores else 50
    
    final_score = (
        avg_review_score * weights['reviews'] +
        rating_score * weights['ratings'] +
        feature_score * weights['features']
    )
    
    # Round to nearest integer
    final_score = round(final_score)
    
    # Prepare detailed scores
    score_details = {
        'final_score': final_score,
        'component_scores': {
            'review_score': round(avg_review_score, 2),
            'rating_score': round(rating_score, 2),
            'feature_score': round(feature_score, 2)
        }
    }
    
    return score_details