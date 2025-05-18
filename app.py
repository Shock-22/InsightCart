import streamlit as st
import json
import pandas as pd
import os
import google.generativeai as genai
from scrape import scrape_amazon
from analyzer import calculate_metacritic_score, generate_product_summary

st.set_page_config(
    page_title="InsightCart - Product Analysis",
    page_icon=":bar_chart:",
    layout="wide",
)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'product_data' not in st.session_state:
    st.session_state.product_data = None

if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = False

# Function to configure Gemini API
def configure_gemini_api(api_key):
    if api_key:
        genai.configure(api_key=api_key)
        st.session_state.api_key_configured = True
        return True
    return False

# Function to generate response using Gemini API
def generate_gemini_response(prompt):
    try:
        # Always read the latest product data from file
        try:
            with open('product_data.json', 'r', encoding='utf-8') as f:
                product_data = json.load(f)
        except Exception as e:
            return f"Error loading product data: {str(e)}"
            
        # Create a context-rich prompt with product data
        context = json.dumps(product_data, indent=2)
        full_prompt = f"""You are a helpful shopping assistant that answers questions about a specific product.
        Here is the product data in JSON format:
        {context}
        
        Based only on the information provided above, please answer the following question:
        {prompt}
        
        If the information is not available in the product data, please say so politely."""
        
        # Generate response using Gemini API with a compatible model
        # Using gemini-pro instead of gemini-1.0-base which is not available
        # for model in genai.list_models():
        #     print(model.name)
        model = genai.GenerativeModel('gemma-3-4b-it')
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def display_metacritic_score(score_details):
    # Create a clean layout for the metacritic score
    st.markdown("""
    <style>
    .metacritic-score {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .high-score { color: #6c3; background-color: #f0f8f0; }
    .mid-score { color: #fc3; background-color: #f8f7f0; }
    .low-score { color: #f00; background-color: #f8f0f0; }
    </style>
    """, unsafe_allow_html=True)

    final_score = score_details['final_score']
    score_class = 'high-score' if final_score >= 75 else 'mid-score' if final_score >= 50 else 'low-score'
    
    st.markdown(f"""
    <div class='metacritic-score {score_class}'>
        {final_score}
    </div>
    """, unsafe_allow_html=True)

    # Display component scores
    st.markdown("### Score Breakdown")
    component_scores = score_details['component_scores']
    
    # Create a DataFrame for component scores
    scores_df = pd.DataFrame({
        'Component': ['Review Analysis', 'Rating Distribution', 'Feature Analysis'],
        'Score': [
            component_scores['review_score'],
            component_scores['rating_score'],
            component_scores['feature_score']
        ]
    })
    
    # Display as a styled table
    st.dataframe(
        scores_df,
        hide_index=True,
        column_config={
            'Component': st.column_config.TextColumn('Component'),
            'Score': st.column_config.ProgressColumn(
                'Score',
                format='%d',
                min_value=0,
                max_value=100,
            )
        }
    )

def display_product_data(data):
    if 'error' in data:
        st.error(f"Error: {data['error']}")
        return

    # Add custom CSS for layout
    st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    
    /* Product Title and Badge */
    .product-title {
        font-size: 32px;
        color: #90caf9;
        margin-bottom: 24px;
        font-weight: 600;
        letter-spacing: -0.5px;
        line-height: 1.2;
        transition: color 0.3s ease;
    }
    .product-title:hover {
        color: #64b5f6;
    }
    .launch-badge {
        background: linear-gradient(45deg, #ff4081, #e91e63);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 2px 4px rgba(233, 30, 99, 0.2);
        display: inline-block;
        margin-bottom: 16px;
    }
    
    /* Price Tag */
    .price-tag {
        font-size: 42px;
        background: linear-gradient(45deg, #2e7d32, #43a047);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin: 20px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Specifications */
    .spec-container {
        background: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(255,255,255,0.1);
        margin: 16px 0;
        transition: transform 0.2s ease;
    }
    .spec-container:hover {
        transform: translateY(-2px);
    }
    .spec-label {
        color: #90a4ae;
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .spec-value {
        font-weight: 600;
        color: #e0e0e0;
        font-size: 16px;
        line-height: 1.5;
    }
    
    /* Review Container */
    .review-stats {
        background-color: #1e1e1e;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(255,255,255,0.08);
        margin: 24px 0;
    }
    
    /* Common Phrases */
    .common-phrase {
        background: #1e1e1e;
        color: #90caf9;
        padding: 8px 16px;
        border-radius: 20px;
        margin: 8px 0;
        display: inline-block;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .common-phrase:hover {
        background: #2c2c2c;
        transform: scale(1.02);
    }
    
    /* Rating Distribution */
    .rating-bar {
        background: linear-gradient(90deg, #ffd54f 0%, #ffb300 100%);
        border-radius: 4px;
        height: 8px;
        transition: width 0.3s ease;
    }
    .rating-container {
        background: #1e1e1e;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(255,255,255,0.05);
        margin: 8px 0;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 24px;
        color: #90caf9;
        margin: 32px 0 16px;
        font-weight: 600;
        border-bottom: 3px solid #2c2c2c;
        padding-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create top layout for title and image with improved spacing
    title_col, analysis_col, right_col = st.columns([1.2, 1, 1])

    with title_col:
        # NEW LAUNCH badge with animation
        st.markdown("<span class='launch-badge'>NEW LAUNCH</span>", unsafe_allow_html=True)
        
        # Product Title with hover effect
        full_title = data['title']
        short_title = full_title.split('|')[0].strip()
        st.markdown(f"<h1 class='product-title'>{short_title}</h1>", unsafe_allow_html=True)
        
        # Main product image with shadow and hover effect
        if data['image_urls']:
            st.markdown("""
                <style>
                .product-image {
                    border-radius: 12px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }
                .product-image:hover {
                    transform: scale(1.02);
                }
                </style>
            """, unsafe_allow_html=True)
            st.image(data['image_urls'][0], use_container_width=True, output_format='auto')

    with analysis_col:
        # Product Analysis section with modern styling
        st.markdown("<h2 class='section-header'>🔍 Product Analysis</h2>", unsafe_allow_html=True)
        summary = generate_product_summary(data)
        analysis_points = summary.split('\n')
        
        # Create a container for analysis points
        st.markdown("<div class='spec-container'>", unsafe_allow_html=True)
        for point in analysis_points:
            if point.strip():
                st.markdown(f"<div class='spec-value'>{point.strip()}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        # Price display with gradient effect
        if data['price']:
            st.markdown(f"<div class='price-tag'>₹{data['price']}</div>", unsafe_allow_html=True)

        # Review Analysis with modern card design
        st.markdown("<h2 class='section-header'>📊 Review Analysis</h2>", unsafe_allow_html=True)
        score_details = calculate_metacritic_score(data)
        display_metacritic_score(score_details)

        # Common Phrases with interactive badges
        st.markdown("<h2 class='section-header'>💬 Common Phrases</h2>", unsafe_allow_html=True)
        common_phrases = ["Great Value", "Excellent Display", "Average Battery"]
        for phrase in common_phrases:
            st.markdown(f"<span class='common-phrase'>{phrase}</span>", unsafe_allow_html=True)

        # Rating Distribution with modern styling
        if data.get('rating_distribution'):
            st.markdown("<h2 class='section-header'>⭐ Rating Distribution</h2>", unsafe_allow_html=True)
            total_ratings = sum(data['rating_distribution'].values())
            if total_ratings > 0:
                for stars in ['5', '4', '3', '2', '1']:
                    percentage = data['rating_distribution'][stars]
                    st.markdown(f"""
                        <div class='rating-container'>
                            <div style='display: flex; align-items: center; justify-content: space-between;'>
                                <span style='color: #ffa000; font-weight: 500;'>{stars}★</span>
                                <div style='flex-grow: 1; margin: 0 10px;'>
                                    <div class='rating-bar' style='width: {percentage}%;'></div>
                                </div>
                                <span style='color: #455a64; font-weight: 500;'>{percentage}%</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # Display specifications in modern card layout
    st.markdown("<h2 class='section-header'>📋 Specifications</h2>", unsafe_allow_html=True)
    if data['specifications']:
        spec_cols = st.columns(3)
        for idx, (key, value) in enumerate(data['specifications'].items()):
            with spec_cols[idx % 3]:
                st.markdown(f"""
                    <div class='spec-container'>
                        <div class='spec-label'>{key}</div>
                        <div class='spec-value'>{value}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Display all Reviews with modern styling
    if data['reviews']:
        st.markdown("<h2 class='section-header'>📝 Customer Reviews</h2>", unsafe_allow_html=True)
        for review in data['reviews']:
            # Calculate rating display
            rating = float(review.get('rating', '0'))
            rating_int = int(rating)
            stars_filled = '★' * rating_int
            stars_empty = '★' * (5 - rating_int)
            
            # Create review container
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Review title
                    st.markdown(f"### {review.get('title', 'Customer Review')}")
                    
                    # Rating and date
                    st.markdown(f"""
                        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 10px;'>
                            <span style='color: #ffd700; font-size: 20px; letter-spacing: 2px'>{stars_filled}<span style='color: rgba(255, 215, 0, 0.3)'>{stars_empty}</span></span>
                            <span style='color: #ffd700'>{rating}/5</span>
                            <span style='color: #90caf9; opacity: 0.8'>{review.get('review_date', '')}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Review content
                    st.markdown(f"""
                        <div style='background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            {review.get('content', '')}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Reviewer name
                    st.markdown(f"""
                        <div style='color: #90caf9; margin-top: 10px;'>
                            Reviewed by <span style='color: #64b5f6; font-weight: 500'>{review.get('reviewer_name', 'Anonymous')}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)

def display_chatbot_interface():
    st.markdown("### Product Chatbot")
    st.markdown("Ask questions about the product and get AI-powered answers.")
    
    # API Key input
    api_key = ""
    configure_gemini_api(api_key)
    
    # Chat interface
    if st.session_state.product_data and st.session_state.api_key_configured:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # User input
        user_question = st.chat_input("Ask a question about the product...")
        
        if user_question:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_question)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_gemini_response(user_question)
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    elif not st.session_state.product_data:
        st.info("Please analyze a product first to use the chatbot.")
    elif not st.session_state.api_key_configured:
        st.info("Please configure your Gemini API key to use the chatbot.")
    
    

# Streamlit UI
st.title('InsightCart - Product Analysis')

info_tab, model_tab = st.tabs(["Product Info", "ChatBot"])

with info_tab:
    url = st.text_input('Enter Amazon Product URL')

    if st.button('Analyze Product'):
        if url:
            if 'amazon' in url.lower():
                # Scrape product data
                data = scrape_amazon(url)
                
                # Save to file
                with open('product_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                st.success('Data saved to product_data.json')
                
                # Store product data in session state for chatbot
                st.session_state.product_data = data
                
                # Display the data in a formatted way
                display_product_data(data)
            else:
                st.error('Please enter a valid Amazon URL')
        else:
            st.warning('Please enter a product URL')

    # Load existing product data if available
    if not st.session_state.product_data and os.path.exists('product_data.json'):
        try:
            with open('product_data.json', 'r', encoding='utf-8') as f:
                st.session_state.product_data = json.load(f)
        except Exception as e:
            st.error(f"Error loading product data: {str(e)}")

with model_tab:
    # Display chatbot interface
    display_chatbot_interface()

