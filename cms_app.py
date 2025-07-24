import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from textblob import TextBlob
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Helper function to get favicon/logo url from domain
def get_favicon_url(url):
    domain = urlparse(url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}"

# Function to get sentiment and color
def sentiment_color(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "green"
    elif polarity < -0.1:
        return "red"
    else:
        return "gray"

# Sidebar - Select Index & timeframe
st.sidebar.title("CMS Indicator Setup")
index_ticker = st.sidebar.selectbox("Select Index/Stock", ["^NSEI", "^BSESN", "^CNXIT", "^NSEBANK", "^CNXPHARMA"])
timeframe = st.sidebar.selectbox("Select Timeframe", ["1d", "5d", "1mo", "3mo"])

# Fetch data
data = yf.download(index_ticker, period=timeframe, interval='1d', auto_adjust=True)

# Plot candlestick + line chart
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Candlestick'
))

fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'],
    mode='lines',
    name='Closing Price',
    line=dict(color='blue', width=1)
))

fig.update_layout(title=f"{index_ticker} Price Chart ({timeframe})",
                  xaxis_title='Date',
                  yaxis_title='Price',
                  xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# --- Fetch news from NewsAPI (replace with your key and API call) ---
# For demo, static example
news = [
    {
        "title": "Market shows positive signs as inflation cools",
        "url": "https://example.com/article1",
        "source": {"name": "Economic Times"},
    },
    {
        "title": "Banking sector hits new low amid policy uncertainty",
        "url": "https://example.com/article2",
        "source": {"name": "Mint"},
    },
    # ... more news articles
]

st.header("Market News & Sentiment")

for article in news:
    title = article["title"]
    url = article["url"]
    source = article["source"]["name"]
    color = sentiment_color(title)
    favicon_url = get_favicon_url(url)
    
    st.markdown(f"""
    <div style="display:flex; align-items:center; margin-bottom:10px;">
        <img src="{favicon_url}" style="width:20px; height:20px; margin-right:8px;" alt="{source} logo"/>
        <a href="{url}" target="_blank" style="color:{color}; font-weight:bold; font-size:16px;">{title}</a>
    </div>
    """, unsafe_allow_html=True)
