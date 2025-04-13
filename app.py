import streamlit as st
import json
import pandas as pd
from scrape import scrape_amazon
from analyzer import calculate_metacritic_score

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

    # Create a clean layout with two columns for main content
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        # Display Title with custom styling
        st.markdown(f"<h1 style='font-size: 24px; color: #1E88E5;'>{data['title']}</h1>", unsafe_allow_html=True)
        
        # Display main product image with proper sizing
        if data['image_urls']:
            st.image(data['image_urls'][0], use_column_width=True)

    with main_col2:
        # Display Price with custom styling
        if data['price']:
            st.markdown(f"<h2 style='font-size: 28px; color: #2E7D32;'>₹{data['price']}</h2>", unsafe_allow_html=True)
        
        # Calculate and display metacritic score
        score_details = calculate_metacritic_score(data)
        display_metacritic_score(score_details)

    # Display Specifications in a clean table format
    if data['specifications']:
        st.markdown("<h3 style='margin-top: 30px;'>Product Specifications</h3>", unsafe_allow_html=True)
        specs_df = pd.DataFrame(list(data['specifications'].items()), columns=['Specification', 'Value'])
        st.dataframe(specs_df, hide_index=True, use_container_width=True)

    # Display Rating Distribution
    if data.get('rating_distribution'):
        st.markdown("<h3 style='margin-top: 30px;'>Rating Distribution</h3>", unsafe_allow_html=True)
        
        # Convert rating distribution to percentage bars
        total_ratings = sum(data['rating_distribution'].values())
        if total_ratings > 0:
            for stars in ['5', '4', '3', '2', '1']:
                percentage = data['rating_distribution'][stars]
                st.markdown(f"{stars} ★")
                st.progress(percentage / 100)
                st.markdown(f"<div style='text-align: right; color: #666;'>{percentage}%</div>", unsafe_allow_html=True)

    # Display Reviews with enhanced styling
    if data['reviews']:
        st.markdown("<h3 style='margin-top: 30px;'>Customer Reviews</h3>", unsafe_allow_html=True)
        for review in data['reviews']:
            with st.container():
                st.markdown("<div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
                
                # Review header with rating
                header_col1, header_col2 = st.columns([4, 1])
                with header_col1:
                    st.markdown(f"**{review.get('title', 'Review')}**")
                with header_col2:
                    if review.get('rating'):
                        st.markdown(f"<span style='color: #FFA000;'>★ {review['rating']}</span>", unsafe_allow_html=True)
                
                # Review content
                st.markdown(f"<div style='margin: 10px 0;'>{review.get('content', '')}</div>", unsafe_allow_html=True)
                
                # Reviewer info
                if review.get('reviewer_name'):
                    st.markdown(f"<div style='color: #666; font-size: 0.9em;'>By {review['reviewer_name']} on {review.get('review_date', '')}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()

# Streamlit UI
st.title('InsightCart - Product Analysis')

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
            
            # Display the data in a formatted way
            display_product_data(data)
        else:
            st.error('Please enter a valid Amazon URL')
    else:
        st.warning('Please enter a product URL')