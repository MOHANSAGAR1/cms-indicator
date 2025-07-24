import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="CMS - Indian Market Sentiment", layout="wide")

# Function to fetch stock/index data safely
def fetch_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True)
        if df.empty:
            st.warning(f"No data found for {ticker}")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# NewsAPI Key input (you can set this in Secrets or enter manually)
api_key = st.sidebar.text_input("Enter your NewsAPI.org API Key:", type="password")

# Indian market indices dictionary with Yahoo Finance symbols
indices = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^NSEPHARMA",
    # Add more valid tickers as needed
}

st.sidebar.header("Select Market Index")
selected_index = st.sidebar.selectbox("Choose Index", list(indices.keys()))

ticker_symbol = indices[selected_index]

st.title(f"CMS - Market Sentiment for {selected_index}")

# Fetch price data
df_price = fetch_data(ticker_symbol)
if df_price.empty:
    st.stop()

# Fetch news articles related to the selected index (past 1 day)
def fetch_news(query, api_key):
    if not api_key:
        st.warning("Please enter your NewsAPI key to fetch news.")
        return []
    url = ('https://newsapi.org/v2/everything?'
           f'q={query}&'
           'language=en&'
           'sortBy=publishedAt&'
           f'from={(datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")}&'
           f'apiKey={api_key}')
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"NewsAPI error: {response.status_code} - {response.text}")
        return []
    data = response.json()
    return data.get('articles', [])

articles = fetch_news(selected_index, api_key)

# Sentiment analysis on headlines
def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

if articles:
    sentiments = [analyze_sentiment(article['title']) for article in articles]
    pos = sum(1 for s in sentiments if s > 0)
    neg = sum(1 for s in sentiments if s < 0)
    neu = sum(1 for s in sentiments if s == 0)
    total = len(sentiments)
    pos_percent = round(pos / total * 100, 2) if total else 0
    neg_percent = round(neg / total * 100, 2) if total else 0
    neu_percent = round(neu / total * 100, 2) if total else 0
else:
    pos_percent = neg_percent = neu_percent = 0

# Display sentiment summary
col1, col2, col3 = st.columns(3)
col1.metric("Positive Sentiment", f"{pos_percent}%")
col2.metric("Negative Sentiment", f"{neg_percent}%")
col3.metric("Neutral Sentiment", f"{neu_percent}%")

# Price Chart (Candlestick + Line)
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df_price.index,
    open=df_price['Open'],
    high=df_price['High'],
    low=df_price['Low'],
    close=df_price['Close'],
    name='Candlestick'
))

fig.add_trace(go.Scatter(
    x=df_price.index,
    y=df_price['Close'],
    mode='lines',
    name='Close Price',
    line=dict(color='blue')
))

fig.update_layout(
    title=f"{selected_index} Price Chart",
    xaxis_title="Date",
    yaxis_title="Price (INR)",
    xaxis_rangeslider_visible=False,
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Display news articles with color-coded headlines and source logo
st.header("Latest News Articles")

for article in articles:
    sentiment = analyze_sentiment(article['title'])
    color = "green" if sentiment > 0 else "red" if sentiment < 0 else "gray"
    source_name = article['source']['name']
    url = article['url']
    published_at = article['publishedAt'][:10]
    logo_url = f"https://logo.clearbit.com/{source_name.replace(' ', '').lower()}.com"

    st.markdown(f"""
        <div style="border-bottom:1px solid #eee; padding:10px 0;">
            <img src="{logo_url}" alt="{source_name}" width="24" style="vertical-align:middle; margin-right:10px;"/>
            <a href="{url}" target="_blank" style="color:{color}; font-weight:bold; font-size:16px;">{article['title']}</a>
            <div style="color:#666; font-size:12px;">{source_name} | {published_at}</div>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("**CMS** - Indian Market Sentiment | Powered by NewsAPI, Yahoo Finance, and Streamlit")

