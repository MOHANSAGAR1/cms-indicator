import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from textblob import TextBlob
from datetime import datetime

# --- Config ---
st.set_page_config(page_title="CMS - Market Sentiment Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Indices & Forex ---
indices = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK"
}

forex_pairs = {
    "USD/INR": "INR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X"
}

timeframe_options = {
    "1 Day": ("1d", "5m"),
    "5 Days": ("5d", "15m"),
    "1 Month": ("1mo", "1d"),
}

sentiment_colors = {
    "positive": "#27ae60",
    "negative": "#c0392b",
    "neutral": "#7f8c8d",
}

@st.cache_data(ttl=300)
def fetch_market_data(symbol, period, interval):
    try:
        df = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        df['Change %'] = df['Close'].pct_change() * 100
        return df
    except Exception:
        return None

def plot_candlestick(df, title):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='Price'
    )])
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        template='plotly_white'
    )
    return fig

def fetch_headlines():
    rss_url = "https://news.google.com/rss/search?q=nifty+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    headlines = []
    for entry in feed.entries[:10]:
        title = entry.title
        blob = TextBlob(title)
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        headlines.append({"title": title, "sentiment": sentiment})
    return headlines

def sentiment_summary(headlines):
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for h in headlines:
        counts[h["sentiment"]] += 1
    total = sum(counts.values())
    for k in counts:
        counts[k] = round((counts[k]/total)*100, 1) if total > 0 else 0
    return counts

# --- Sidebar ---
st.sidebar.title("CMS - Market Sentiment Setup")
selected_index = st.sidebar.selectbox("Select Market Index", list(indices.keys()))
selected_forex = st.sidebar.selectbox("Select Forex Pair", list(forex_pairs.keys()))
selected_timeframe = st.sidebar.selectbox("Select Timeframe", list(timeframe_options.keys()))

# --- Main Header ---
st.title("📊 CMS Market Sentiment Dashboard")

# --- Headlines & Sentiment ---
st.subheader("📰 Live Market News Sentiment")
headlines = fetch_headlines()
summary = sentiment_summary(headlines)

col1, col2, col3 = st.columns(3)
col1.metric("Positive Sentiment", f"{summary['positive']}%")
col2.metric("Neutral Sentiment", f"{summary['neutral']}%")
col3.metric("Negative Sentiment", f"{summary['negative']}%")

st.markdown("---")
for h in headlines:
    color = sentiment_colors.get(h["sentiment"], "#000000")
    st.markdown(
        f"<span style='color:{color}; font-weight:600'>{h['sentiment'].capitalize()}</span> — {h['title']}",
        unsafe_allow_html=True
    )

# --- Market Chart ---
period, interval = timeframe_options[selected_timeframe]
df_index = fetch_market_data(indices[selected_index], period, interval)
if df_index is not None:
    st.subheader(f"{selected_index} Price Chart ({selected_timeframe})")
    st.plotly_chart(plot_candlestick(df_index, f"{selected_index} - {selected_timeframe}"), use_container_width=True)
    st.metric(label="Daily Change %", value=f"{df_index['Change %'].iloc[-1]:.2f}%")
else:
    st.warning(f"Could not load data for {selected_index}")

# --- Forex Chart ---
df_forex = fetch_market_data(forex_pairs[selected_forex], period, interval)
if df_forex is not None:
    st.subheader(f"{selected_forex} Price Chart ({selected_timeframe})")
    st.plotly_chart(plot_candlestick(df_forex, f"{selected_forex} - {selected_timeframe}"), use_container_width=True)
    st.metric(label="Daily Change %", value=f"{df_forex['Change %'].iloc[-1]:.2f}%")
else:
    st.warning(f"Could not load data for {selected_forex}")

# --- Footer ---
st.markdown("---")
st.caption("📈 Powered by Yahoo Finance & Google News | Built by Mohan Sagar")
