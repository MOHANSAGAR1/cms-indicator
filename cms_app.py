import streamlit as st
import requests
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
from datetime import datetime, timedelta

# Streamlit App Title
st.set_page_config(page_title="CMS - Crowd Market Sentiment", layout="wide")
st.title("🧠 CMS - Crowd Market Sentiment (India)")

# API Key Input
api_key = st.secrets["news_api_key"] if "news_api_key" in st.secrets else st.text_input("Enter your NewsAPI.org API Key:", type="password")

# Topic selection
query = st.text_input("Enter a market-related topic (e.g., Nifty, Sensex, RBI, Reliance):", "Nifty")

# Function to get news
@st.cache_data(ttl=3600)
def get_news(api_key, query):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&from={(datetime.now() - timedelta(days=1)).date()}&sortBy=publishedAt&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        st.error("❌ Failed to fetch news. Check your API key or try again later.")
        return []

# Sentiment calculation
def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity

# Process and visualize
if api_key:
    articles = get_news(api_key, query)
    if articles:
        titles = [article["title"] for article in articles if article["title"]]
        descriptions = [article["description"] or "" for article in articles]
        combined_text = " ".join(titles + descriptions)

        # Sentiment analysis
        sentiments = [analyze_sentiment(text) for text in titles]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        # Sentiment status
        if avg_sentiment > 0.1:
            status = "🟢 Positive"
        elif avg_sentiment < -0.1:
            status = "🔴 Negative"
        else:
            status = "🟡 Neutral"

        # Layout
        col1, col2 = st.columns([2, 3])

        with col1:
            st.subheader("📊 Sentiment Score")
            st.metric(label="Average Sentiment", value=f"{avg_sentiment:.2f}", delta=status)

            # WordCloud
            st.subheader("☁ Word Cloud from News")
            wordcloud = WordCloud(width=600, height=400, background_color='white').generate(combined_text)
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            st.pyplot(plt)

        with col2:
            st.subheader("🗞 Latest Market News")
            for article in articles[:10]:
                st.markdown(f"**{article['title']}**")
                st.markdown(f"*{article['source']['name']}* — {article['publishedAt'][:10]}")
                st.markdown(article['description'] or "_No description provided._")
                st.markdown(f"[Read More]({article['url']})")
                st.markdown("---")
    else:
        st.warning("No recent articles found.")
else:
    st.info("🔐 Please enter your NewsAPI key to begin.")
