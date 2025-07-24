# CMS - Crowd Market Sentiment Indicator
import streamlit as st
import pandas as pd
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="CMS - Market Sentiment", layout="wide")

st.title("📊 CMS - Crowd Market Sentiment (Live News-Based)")

# Input: Your News API Key
api_key = st.secrets["NEWSAPI_KEY"] if "NEWSAPI_KEY" in st.secrets else st.text_input("🔑 Enter your NewsAPI.org API Key:", type="password")

# Topic or keyword
topic = st.text_input("🔍 Enter a keyword (e.g., 'Nifty', 'BankNifty', 'RBI', etc.):", "Nifty")

# Date range
from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')

# Run only if API key is provided
if api_key:
    with st.spinner("Fetching sentiment news..."):
        url = f"https://newsapi.org/v2/everything?q={topic}&from={from_date}&to={to_date}&sortBy=publishedAt&language=en&apiKey={api_key}"
        response = requests.get(url)
        data = response.json()

        if data.get("status") == "ok":
            articles = data["articles"]
            if len(articles) == 0:
                st.warning("No articles found for the given keyword.")
            else:
                df = pd.DataFrame(articles)[["title", "description", "publishedAt", "url"]]
                st.subheader("🗞️ Latest News Articles")
                st.dataframe(df)

                # Combine titles and descriptions
                text_blob = " ".join(df["title"].fillna('')) + " " + " ".join(df["description"].fillna(''))

                # Generate WordCloud
                st.subheader("☁️ Word Cloud")
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_blob)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
        else:
            st.error("Failed to fetch data. Check your API key or try later.")
else:
    st.info("Please enter your News API key to fetch sentiment data.")
