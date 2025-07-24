import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- Page config ---
st.set_page_config(page_title="CMS - Market Sentiment Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Market indices and Forex pairs ---
indices = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "MIDCAP 50": "^NSEMIDCAP50",  # May need validation if symbol exists
}

forex_pairs = {
    "USD/INR": "INR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
}

# --- Timeframes map ---
timeframe_options = {
    "1 Day": ("1d", "5m"),      # interval 5 minutes for 1 day
    "5 Days": ("5d", "15m"),    # interval 15 minutes for 5 days
    "1 Month": ("1mo", "1d"),   # daily interval for 1 month
}

# --- Sentiment colors ---
sentiment_colors = {
    "positive": "#27ae60",
    "negative": "#c0392b",
    "neutral": "#7f8c8d",
}

# --- Cached market data fetcher ---
@st.cache_data(ttl=300)
def fetch_market_data(symbol, period, interval):
    try:
        df = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        df['Change %'] = df['Close'].pct_change() * 100
        return df
    except Exception as e:
        return None

# --- Function to plot candlestick chart ---
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

# --- Fake headline data with logos and sentiment (replace with real API or scraping later) ---
def get_headlines():
    # Logos url for example sources
    logos = {
        "Reuters": "https://upload.wikimedia.org/wikipedia/commons/6/60/Reuters_logo.svg",
        "Bloomberg": "https://upload.wikimedia.org/wikipedia/commons/e/e2/Bloomberg_logo.svg",
        "Economic Times": "https://upload.wikimedia.org/wikipedia/en/thumb/4/43/Economic_Times_logo.svg/1200px-Economic_Times_logo.svg.png",
    }
    headlines = [
        {"title": "Nifty rallies 1.5% led by banking stocks", "sentiment": "positive", "source": "Reuters"},
        {"title": "Sensex drops amid global uncertainty", "sentiment": "negative", "source": "Bloomberg"},
        {"title": "Midcap stocks show steady growth", "sentiment": "neutral", "source": "Economic Times"},
    ]
    # Add logo URL to each headline dict
    for h in headlines:
        h["logo_url"] = logos.get(h["source"], "")
    return headlines

# --- Compute sentiment summary from headlines ---
def sentiment_summary(headlines):
    counts = {"positive":0, "negative":0, "neutral":0}
    for h in headlines:
        s = h.get("sentiment", "neutral")
        if s in counts:
            counts[s] += 1
    total = sum(counts.values())
    if total == 0:
        return counts
    for k in counts:
        counts[k] = round((counts[k]/total)*100, 1)
    return counts

# --- Sidebar ---
st.sidebar.title("CMS - Market Sentiment Setup")
selected_index = st.sidebar.selectbox("Select Market Index", list(indices.keys()))
selected_forex = st.sidebar.selectbox("Select Forex Pair", list(forex_pairs.keys()))
selected_timeframe = st.sidebar.selectbox("Select Timeframe", list(timeframe_options.keys()))

# --- Main UI ---

st.title("📊 CMS Market Sentiment Dashboard")
st.markdown(
    """
    <style>
    .metric { font-size: 22px; font-weight: bold; }
    .sentiment-bar {
        height: 15px; 
        border-radius: 8px;
        margin-bottom: 5px;
    }
    .headline { margin-bottom: 10px; }
    .headline-logo { height: 25px; width: auto; margin-right: 8px; vertical-align: middle; }
    .sentiment-tag {
        padding: 2px 8px; 
        border-radius: 12px; 
        font-size: 12px; 
        color: white;
        vertical-align: middle;
        margin-left: 6px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- Sentiment summary ---

headlines = get_headlines()
summary = sentiment_summary(headlines)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric'>Positive Sentiment</div>")
    st.progress(summary["positive"] / 100)
    st.markdown(f"{summary['positive']}%")
with col2:
    st.markdown(f"<div class='metric'>Neutral Sentiment</div>")
    st.progress(summary["neutral"] / 100)
    st.markdown(f"{summary['neutral']}%")
with col3:
    st.markdown(f"<div class='metric'>Negative Sentiment</div>")
    st.progress(summary["negative"] / 100)
    st.markdown(f"{summary['negative']}%")

st.markdown("---")

# --- Market Index Chart ---
period, interval = timeframe_options[selected_timeframe]
df_index = fetch_market_data(indices[selected_index], period, interval)
if df_index is not None and not df_index.empty:
    st.subheader(f"{selected_index} Price Chart ({selected_timeframe})")
    st.plotly_chart(plot_candlestick(df_index, f"{selected_index} - {selected_timeframe}"), use_container_width=True)
    last_change = df_index['Change %'].iloc[-1]
    st.metric(label=f"{selected_index} Daily Change %", value=f"{last_change:.2f}%")
else:
    st.warning(f"Could not fetch data for {selected_index}")

# --- Forex Pair Chart ---
df_forex = fetch_market_data(forex_pairs[selected_forex], period, interval)
if df_forex is not None and not df_forex.empty:
    st.subheader(f"{selected_forex} Price Chart ({selected_timeframe})")
    st.plotly_chart(plot_candlestick(df_forex, f"{selected_forex} - {selected_timeframe}"), use_container_width=True)
    last_change_fx = df_forex['Change %'].iloc[-1]
    st.metric(label=f"{selected_forex} Daily Change %", value=f"{last_change_fx:.2f}%")
else:
    st.warning(f"Could not fetch data for {selected_forex}")

st.markdown("---")

# --- Headlines Section ---
st.header("📰 Latest Market Headlines & Sentiment")

for h in headlines:
    color = sentiment_colors.get(h["sentiment"], "#000000")
    logo_img = f"<img src='{h['logo_url']}' class='headline-logo'>" if h['logo_url'] else ""
    sentiment_tag = f"<span class='sentiment-tag' style='background-color:{color};'>{h['sentiment'].capitalize()}</span>"
    st.markdown(
        f"<div class='headline'>{logo_img}<strong>{h['source']}</strong>: {h['title']} {sentiment_tag}</div>", 
        unsafe_allow_html=True
    )

# --- Footer ---
st.markdown(
    """
    ---
    Powered by Yahoo Finance & CMS | Developed for public use
    """,
    unsafe_allow_html=True,
)
