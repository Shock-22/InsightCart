import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModel, pipeline
import torch
import numpy as np
from typing import Dict, List, Union, Optional
import streamlit as st

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


def generate_product_summary(product_data: Dict) -> str:
    """Generate a concise summary of product features using BERT."""
    if not product_data.get('specifications'):
        return "❌ No product specifications available to generate a summary."
    
    # Extract specifications and key features
    specs = product_data['specifications']
    
    # Prepare text for summarization
    summary_text = []
    
    # Add overall verdict at the top with enhanced formatting
    sentiment = analyze_sentiment(str(product_data))
    summary_text.append("**📝 Product Analysis**")
    summary_text.append("**Overall Verdict**")
    
    if sentiment['compound'] > 0.2:
        verdict = ["### ⭐⭐⭐⭐⭐ Outstanding Performance",
                  "**Key Highlights:**",
                  "- Premium build quality and exceptional durability",
                  "- Outstanding performance across all metrics",
                  "- Industry-leading features and capabilities",
                  "",
                  "*Perfect for professionals and power users who demand the absolute best.*"]
        summary_text.extend(verdict)
    elif sentiment['compound'] > 0:
        verdict = ["### ⭐⭐⭐⭐ Great Value",
                  "**Key Highlights:**",
                  "- Solid build quality and reliable performance",
                  "- Well-balanced feature set",
                  "- Good value for money",
                  "",
                  "*Excellent choice for everyday users seeking quality and functionality.*"]
        summary_text.extend(verdict)
    else:
        verdict = ["### ⭐⭐⭐ Decent Choice",
                  "**Key Highlights:**",
                  "- Standard build quality",
                  "- Basic feature set",
                  "- Adequate performance",
                  "",
                  "*Suitable for users with moderate usage requirements.*"]
        summary_text.extend(verdict)
    
    summary_text.append("---")
    
    # Add product title with enhanced formatting
    if product_data.get('title'):
        title_parts = product_data['title'].split(' - ') if ' - ' in product_data['title'] else [product_data['title']]
        summary_text.append("**✨ Product Overview**")
        summary_text.append(f"**{title_parts[0]}**")
        if len(title_parts) > 1:
            summary_text.append(f"*{title_parts[1]}*")
        
        # Extract and format key specs for overview
        key_specs = [spec for spec in specs.values() if isinstance(spec, str) and any(keyword in spec.lower() for keyword in ['chipset', 'battery', 'display', 'camera'])]
        if key_specs:
            summary_text.append("")
            summary_text.append("**Quick Specs:**")
            for spec in key_specs:
                summary_text.append(f"- {spec}")
    
    summary_text.append("---")
    
    # Add key features with enhanced formatting
    if 'Key Features' in specs and isinstance(specs['Key Features'], list):
        key_features = specs['Key Features']
        if key_features:
            summary_text.append("**🌟 Key Features**")
            for i, feature in enumerate(key_features[:5], 1):  # Limit to top 5 features
                feature_parts = feature.split(': ', 1) if ': ' in feature else [feature, '']
                if len(feature_parts) == 2:
                    summary_text.extend([
                        f"**{i}. {feature_parts[0]}**",
                        feature_parts[1],
                        ""
                    ])
                else:
                    summary_text.extend([f"**{i}. {feature}**", ""])

    
    # Add important specifications with enhanced formatting
    priority_specs = {
        'Brand': '🏢',
        'Model': '📱',
        'Operating System': '⚙️',
        'Display': '📱',
        'Battery': '🔋',
        'Chipset': '💻',
        'RAM & Storage': '💾',
        'Camera': '📸',
        'Water/Dust Resistance': '💧',
        'Special Features': '✨',
        'Dimensions': '📏',
        'Weight': '⚖️',
        'Color': '🎨',
        'Connectivity': '📡',
        'Form Factor': '📱'
    }
    
    # Organize specifications into categories
    spec_categories = {
        'Core Specs': ['Brand', 'Model', 'Operating System'],
        'Performance': ['Chipset', 'RAM & Storage'],
        'Display & Camera': ['Display', 'Camera'],
        'Battery & Power': ['Battery'],
        'Design': ['Dimensions', 'Weight', 'Color', 'Form Factor', 'Water/Dust Resistance'],
        'Connectivity': ['Connectivity', 'Special Features']
    }
    
    # Format specifications by category
    if any(key in specs for key in [k for v in spec_categories.values() for k in v]):
        summary_text.append("**📋 Technical Specifications**")
        
        for category, category_specs in spec_categories.items():
            category_items = []
            for spec in category_specs:
                for spec_key, value in specs.items():
                    if any(k.lower() in spec_key.lower() for k in [spec, spec.replace(' & ', ' '), spec.replace('/', ' ')]):
                        if isinstance(value, list):
                            value = ', '.join(value)
                        emoji = priority_specs.get(spec, '•')
                        category_items.append(f"{emoji} **{spec}**: {value}")
                        break
            
            if category_items:
                summary_text.append(f"**{category}**")
                summary_text.extend(category_items)
                summary_text.append("")
    
    # Add a conclusion based on sentiment analysis
    if summary_text:
        full_text = '\n'.join(summary_text)
        sentiment = analyze_sentiment(full_text)
        
        summary_text.append("---")
        summary_text.append("**💡 Final Thoughts**")
        
        if sentiment['compound'] > 0.2:
            summary_text.append("*This product stands out with exceptional features and capabilities, making it a compelling choice for those seeking premium quality and performance.*")
        elif sentiment['compound'] > 0:
            summary_text.append("*A well-rounded product that offers good value for money, suitable for most users' needs.*")
        else:
            summary_text.append("*While meeting basic requirements, consider your specific needs and compare with alternatives before making a decision.*")
    
    return '\n\n'.join(summary_text)