import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

# --- Setup ---
st.set_page_config(page_title="CMS - Market Sentiment Dashboard", layout="wide")

# --- Market indices and Forex pairs ---
indices = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "MIDCAP 50": "^NSEMIDCAP50",  # Validate if available
}

forex_pairs = {
    "USD/INR": "INR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
}

# --- Function to fetch market data ---
@st.cache_data(ttl=300)
def fetch_market_data(symbol):
    try:
        df = yf.download(tickers=symbol, period="7d", interval="1d", auto_adjust=True)
        if df.empty:
            return None
        df['Change %'] = df['Close'].pct_change() * 100
        return df
    except Exception as e:
        return None

# --- Function to fetch sentiment from headlines (dummy example) ---
def fetch_headlines_and_sentiment():
    # For demo, static sample headlines with sentiment
    headlines = [
        {"title": "Nifty rallies 1.5% led by banking stocks", "sentiment": "positive", "source": "Reuters"},
        {"title": "Sensex drops amid global uncertainty", "sentiment": "negative", "source": "Bloomberg"},
        {"title": "Midcap stocks show steady growth", "sentiment": "neutral", "source": "Economic Times"},
    ]
    return headlines

# --- Color mapping for sentiments ---
sentiment_colors = {
    "positive": "#2ecc71",  # green
    "negative": "#e74c3c",  # red
    "neutral": "#95a5a6",   # gray
}

# --- Helper to create candlestick charts ---
def plot_candlestick(df, title):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
    )])
    fig.update_layout(title=title, xaxis_title='Date', yaxis_title='Price', height=350, margin=dict(l=20,r=20,t=30,b=20))
    return fig

# --- Sidebar ---
st.sidebar.title("CMS Market Sentiment Dashboard")
selected_index = st.sidebar.selectbox("Select Market Index", list(indices.keys()))
selected_forex = st.sidebar.selectbox("Select Forex Pair", list(forex_pairs.keys()))
refresh = st.sidebar.button("Refresh Data")

# --- Main page ---

st.title("📈 CMS Market Sentiment Dashboard")
st.markdown(
    """
    **Real-time Indian Market Indices & Forex Sentiment Indicator**  
    A simple yet powerful dashboard showing live price charts, sentiment overview, and latest market news.
    """
)

# --- Fetch and show market index data ---
symbol_index = indices[selected_index]
df_index = fetch_market_data(symbol_index)
if df_index is not None and not df_index.empty:
    st.subheader(f"{selected_index} Price Chart")
    st.plotly_chart(plot_candlestick(df_index, f"{selected_index} - Last 7 Days"), use_container_width=True)
    last_change = df_index['Change %'].iloc[-1]
    st.metric(label=f"{selected_index} Daily Change %", value=f"{last_change:.2f}%")
else:
    st.warning(f"Could not fetch data for {selected_index}")

# --- Fetch and show forex data ---
symbol_forex = forex_pairs[selected_forex]
df_forex = fetch_market_data(symbol_forex)
if df_forex is not None and not df_forex.empty:
    st.subheader(f"{selected_forex} Price Chart")
    st.plotly_chart(plot_candlestick(df_forex, f"{selected_forex} - Last 7 Days"), use_container_width=True)
    last_change_fx = df_forex['Change %'].iloc[-1]
    st.metric(label=f"{selected_forex} Daily Change %", value=f"{last_change_fx:.2f}%")
else:
    st.warning(f"Could not fetch data for {selected_forex}")

# --- Sentiment summary section ---
st.markdown("---")
st.header("📰 Latest Market Headlines & Sentiment")

headlines = fetch_headlines_and_sentiment()
for h in headlines:
    color = sentiment_colors.get(h["sentiment"], "#000000")
    st.markdown(
        f'<p style="font-size:16px; color:{color}; font-weight:bold;">[{h["source"]}] {h["title"]}</p>', 
        unsafe_allow_html=True
    )

# --- Footer ---
st.markdown(
    """
    ---
    Powered by Yahoo Finance & CMS | Created for public use
    """,
    unsafe_allow_html=True,
)

