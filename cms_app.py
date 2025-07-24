import streamlit as st
import yfinance as yf
import requests
from textblob import TextBlob
from datetime import datetime, timedelta

# --- Helper functions for sentiment ---
def get_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.05:
        return "Positive"
    elif analysis.sentiment.polarity < -0.05:
        return "Negative"
    else:
        return "Neutral"

def fetch_news(query, api_key):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={api_key}"
    res = requests.get(url).json()
    return res.get("articles", [])

# --- Indian market indices ---
INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^NSEPHARMA",
    "Nifty FMCG": "^CNXFMCG"
}

# --- Streamlit app start ---
st.set_page_config(page_title="CMS - Market Sentiment", layout="wide")
st.title("📈 CMS: Comprehensive Market Sentiment Indicator")
st.markdown("## Real-time Indian Market Sentiment Based on News")

# Sidebar
api_key = st.sidebar.text_input("Enter your NewsAPI.org API Key", type="password")
index_choice = st.sidebar.selectbox("Select Market Index", list(INDICES.keys()))

if api_key and index_choice:
    with st.spinner("Fetching news and calculating sentiment..."):
        news = fetch_news(index_choice, api_key)

        sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for article in news:
            sentiment = get_sentiment(article["title"] + " " + article.get("description", ""))
            sentiments[sentiment] += 1

        total_news = sum(sentiments.values())
        if total_news > 0:
            pos_pct = (sentiments["Positive"] / total_news) * 100
            neg_pct = (sentiments["Negative"] / total_news) * 100
            neu_pct = (sentiments["Neutral"] / total_news) * 100
        else:
            pos_pct = neg_pct = neu_pct = 0

        # Layout with columns
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader(f"News Headlines for {index_choice}")
            for article in news:
                st.markdown(f"**[{article['title']}]({article['url']})**")
                st.write(article.get("description", ""))
                st.write("---")

        with col2:
            st.subheader("Sentiment Overview")
            st.metric("Positive", f"{pos_pct:.1f} %", delta=f"{pos_pct - 50:.1f}%")
            st.metric("Negative", f"{neg_pct:.1f} %", delta=f"{neg_pct - 50:.1f}%")
            st.metric("Neutral", f"{neu_pct:.1f} %")

            st.progress(pos_pct / 100)
            st.progress(neg_pct / 100)
            st.progress(neu_pct / 100)

        # Show current price and chart
        ticker = INDICES[index_choice]
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        st.subheader(f"{index_choice} Price Chart")
        st.line_chart(df["Close"])

else:
    st.warning("🔐 Please enter your NewsAPI.org API Key and select an index from the sidebar.")

