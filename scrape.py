import requests
from bs4 import BeautifulSoup
import re

def scrape_amazon(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product details
        product_data = {
            'title': soup.select_one('#productTitle').text.strip() if soup.select_one('#productTitle') else '',
            'price': soup.select_one('.a-price-whole').text.strip() if soup.select_one('.a-price-whole') else '',
            'image_urls': [],
            'specifications': {},
            'reviews': [],
            'rating_distribution': {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        }
        
        # Extract images with multiple selector options
        image_containers = soup.select('#altImages, #imageBlock, #imgTagWrapperId')
        for container in image_containers:
            image_elements = container.select('img, div.imgTagWrapper img')
            for img in image_elements:
                if 'src' in img.attrs:
                    img_url = img['src']
                    # Convert thumbnail URLs to full-size image URLs
                    img_url = re.sub(r'\._[^.]*\.(jpg|png)', '.' + '\\1', img_url)
                    if not img_url.endswith('gif') and 'sprite' not in img_url:
                        if img_url not in product_data['image_urls']:
                            product_data['image_urls'].append(img_url)
        
        # Get main product image with multiple selector options
        main_img = soup.select_one('#landingImage, #main-image, #img-canvas img')
        if main_img and 'src' in main_img.attrs:
            main_img_url = main_img['src']
            if main_img_url not in product_data['image_urls']:
                product_data['image_urls'].insert(0, main_img_url)
        
        # Extract specifications from multiple possible locations
        # Try the technical details table first
        specs_table = soup.select('#productDetails_techSpec_section_1 tr, #productDetails_db_sections tr, .prodDetTable tr, .a-keyvalue tr')
        for row in specs_table:
            if row.select_one('th') and row.select_one('td'):
                key = row.select_one('th').text.strip()
                value = row.select_one('td').text.strip()
                product_data['specifications'][key] = value
        
        # Try the product information section
        info_sections = soup.select('#productOverview_feature_div table tr, #detailBullets_feature_div li, #feature-bullets li')
        for section in info_sections:
            # Handle detail bullets format
            if section.select_one('.a-list-item'):
                text = section.select_one('.a-list-item').text.strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    product_data['specifications'][key.strip()] = value.strip()
            # Handle table format
            elif section.select_one('td'):
                cells = section.select('td, th')
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    if key and value:
                        product_data['specifications'][key] = value
        
        # Try the feature bullets
        feature_list = soup.select('#feature-bullets ul li:not(.aok-hidden) span.a-list-item')
        if feature_list:
            product_data['specifications']['Key Features'] = [item.text.strip() for item in feature_list]
        
        # Extract rating distribution
        rating_bars = soup.select('tr[data-hook="rating-distribution-row"]')
        for bar in rating_bars:
            rating = bar.select_one('td:first-child a')
            percentage = bar.select_one('td:last-child span')
            if rating and percentage:
                rating_text = rating.text.strip().split()[0]  # Get the star number
                percentage_text = percentage.text.strip().replace('%', '')
                try:
                    product_data['rating_distribution'][rating_text] = float(percentage_text)
                except ValueError:
                    continue

        # Extract reviews with specific data-hook attributes from Amazon HTML structure
        reviews = soup.select('div[data-hook="review"], li[id][data-hook="review"]')
        for review in reviews[:10]:  # Increased limit to capture more reviews
            try:
                review_data = {
                    'title': '',
                    'content': '',
                    'rating': '',
                    'reviewer_name': '',
                    'review_date': ''
                }
                
                # Extract review title - look for review-title data-hook
                title_elem = review.select_one('a[data-hook="review-title"], span[data-hook="review-title"]')
                if title_elem:
                    review_data['title'] = title_elem.text.strip()
                
                # Extract review content - look for review-body data-hook
                content_elem = review.select_one('span[data-hook="review-body"]')
                if content_elem:
                    # Get the actual text content, which might be in a nested span
                    text_span = content_elem.select_one('span')
                    if text_span:
                        review_data['content'] = text_span.text.strip()
                    else:
                        review_data['content'] = content_elem.text.strip()
                
                # Also check for collapsed review content
                collapsed_elem = review.select_one('div[data-hook="review-collapsed"]')
                if collapsed_elem and not review_data['content']:
                    review_data['content'] = collapsed_elem.text.strip()
                
                # Extract rating - look for review-star-rating data-hook
                rating_elem = review.select_one('i[data-hook="review-star-rating"], i[data-hook="cmps-review-star-rating"]')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    # Extract just the number from "X.X out of 5"
                    rating_match = re.search(r'([\d.]+)\s*out of\s*\d', rating_text)
                    if rating_match:
                        review_data['rating'] = rating_match.group(1)
                    else:
                        review_data['rating'] = rating_text
                
                # Extract reviewer name - look for profile name
                reviewer_elem = review.select_one('span.a-profile-name')
                if reviewer_elem:
                    review_data['reviewer_name'] = reviewer_elem.text.strip()
                
                # Extract date - look for review-date data-hook
                date_elem = review.select_one('span[data-hook="review-date"]')
                if date_elem:
                    review_data['review_date'] = date_elem.text.strip()
                
                if any(value for value in review_data.values()):
                    product_data['reviews'].append(review_data)
            except Exception as e:
                continue
        
        return product_data
    except Exception as e:
        return {'error': str(e)}