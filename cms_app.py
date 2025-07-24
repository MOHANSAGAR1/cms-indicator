import streamlit as st

# --- Example sentiment percentages (replace with your real data) ---
positive_percent = 65
negative_percent = 25
neutral_percent = 10

# --- Market indices with their ticker symbols ---
indices = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "Midcap 50": "^MIDCAP50",
    # add more Indian indices as needed
}

# --- Forex currency pairs (Yahoo Finance format) ---
forex_pairs = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "USD/INR": "USDINR=X",
    "AUD/USD": "AUDUSD=X",
    # add more forex pairs as you want
}

# Merge both dictionaries for selection
all_markets = {**indices, **forex_pairs}

# --- App Title ---
st.title("CMS — Crypto Market Sentiment Indicator")

# --- Sentiment Indicator Panel at the top ---
st.markdown(
    f"""
    <style>
    .sentiment-container {{
        display: flex;
        justify-content: center;
        gap: 3rem;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 12px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    }}
    .positive {{ color: #2ecc71; }}
    .negative {{ color: #e74c3c; }}
    .neutral {{ color: #95a5a6; }}
    </style>
    <div class="sentiment-container">
        <div class="positive">👍 Positive: {positive_percent}%</div>
        <div class="negative">👎 Negative: {negative_percent}%</div>
        <div class="neutral">😐 Neutral: {neutral_percent}%</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Selection Box for Market Indices + Forex Pairs ---
selected_market = st.selectbox("Select Market Index or Forex Pair", list(all_markets.keys()))

ticker_symbol = all_markets[selected_market]
st.write(f"Showing data for: **{selected_market}** (Ticker: `{ticker_symbol}`)")

# Placeholder for your live data, charts, news, sentiment calculations, etc.
st.info("Here will be the live news, charts, and sentiment updates related to the selected market or forex pair.")

# --- You can add your fetching and plotting code below ---
# Example: fetch price data using yfinance, render charts, show news, etc.
