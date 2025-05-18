# InsightCart 🛒

InsightCart is an intelligent product analysis tool that helps users make informed purchasing decisions by providing comprehensive analysis of Amazon products using advanced AI and natural language processing techniques.

## 🌟 Features

- **Product Analysis**: Scrapes and analyzes Amazon product data
- **Sentiment Analysis**: Uses VADER sentiment analysis for review evaluation
- **BERT Integration**: Leverages BERT embeddings for feature analysis
- **MetaCritic-Style Scoring**: Provides detailed scoring based on multiple factors
- **Interactive Chat**: AI-powered product-specific chat using Google's Gemini API
- **Visual Analytics**: Clean and intuitive Streamlit interface

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Shock-22/InsightCart.git
cd InsightCart
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Enter an Amazon product URL in the interface
3. View the comprehensive analysis including:
   - MetaCritic-style scoring
   - Sentiment analysis
   - Feature breakdown
   - Interactive chat support

## 📦 Project Structure

- `app.py`: Main Streamlit application interface
- `scrape.py`: Amazon product data scraping functionality
- `analyzer.py`: Core analysis and scoring algorithms
- `fake.py`: Fake review detection model
- `requirements.txt`: Project dependencies

## 🛠️ Technologies Used

- **Web Scraping**: BeautifulSoup4 (4.12.2), Requests (2.31.0)
- **Data Analysis**: Pandas (2.1.4), NumPy (1.26.2)
- **Machine Learning**: PyTorch (2.2.0), Transformers (4.36.2)
- **NLP**: NLTK (3.8.1), VADER Sentiment Analysis
- **AI Integration**: Google Generative AI (0.3.1)
- **Frontend**: Streamlit

## 🔑 Key Components

### Analyzer Module
- Sentiment analysis using VADER
- BERT embeddings for feature analysis
- MetaCritic-style scoring system
- Product summary generation

### Scraper Module
- Amazon product data extraction
- Review and rating collection
- Specification parsing
- Image URL extraction

### Frontend Interface
- Clean, intuitive UI
- Interactive components
- Real-time analysis display
- AI-powered chat support

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please ensure compliance with Amazon's terms of service when using the scraping functionality.
