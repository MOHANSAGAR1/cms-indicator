import streamlit as st
import requests
import yfinance as yf
from textblob import TextBlob
import plotly.graph_objects as go

st.set_page_config(page_title="CMS - Market Sentiment Indicator", layout="wide")

# === API key from Streamlit secrets (set this in your Streamlit Cloud secrets) ===
api_key = st.secrets["NEWSAPI_KEY"]

indices = {
    "NIFTY 50": "^NSEI",
    "BSE SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "NIFTY IT": "^CNXIT"
}

st.title("📊 CMS - Market Sentiment Indicator")
st.markdown("Real-time Indian Market sentiment with price charts and news")

selected_index = st.sidebar.selectbox("Select Market Index", list(indices.keys()))
timeframe = st.sidebar.selectbox("Select Chart Timeframe", ["5d", "1mo", "3mo"])

ticker = indices[selected_index]

@st.cache_data(ttl=300)
def get_price_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        return df
    except Exception:
        return None

df_price = get_price_data(ticker, timeframe)
if df_price is None or df_price.empty:
    st.error("Unable to load price data. Please try another index or timeframe.")
    st.stop()

fig = go.Figure(data=[go.Candlestick(
    x=df_price.index,
    open=df_price['Open'],
    high=df_price['High'],
    low=df_price['Low'],
    close=df_price['Close'],
    increasing_line_color='green',
    decreasing_line_color='red'
)])
fig.update_layout(title=f"{selected_index} Price Chart ({timeframe})",
                  xaxis_title="Date", yaxis_title="Price (INR)",
                  xaxis_rangeslider_visible=False,
                  template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl=300)
def fetch_news_sentiment(query, key, max_articles=15):
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}&"
        "language=en&"
        "sortBy=publishedAt&"
        f"pageSize={max_articles}&"
        f"apiKey={key}"
    )
    res = requests.get(url)
    if res.status_code != 200:
        return []
    data = res.json()
    return data.get("articles", [])

articles = fetch_news_sentiment(selected_index, api_key)

if not articles:
    st.warning("No recent news found.")
else:
    pos, neg, neu = 0, 0, 0
    st.header("📰 Latest Market News & Sentiment")

    for art in articles:
        headline = art['title']
        desc = art.get('description', '')
        url = art['url']
        source = art.get('source', {}).get('name', 'Unknown')
        pub_date = art.get('publishedAt', '')[:10]

        text = f"{headline} {desc}"
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.05:
            sentiment = "Positive"
            color = "green"
            pos += 1
        elif polarity < -0.05:
            sentiment = "Negative"
            color = "red"
            neg += 1
        else:
            sentiment = "Neutral"
            color = "gray"
            neu += 1

        st.markdown(f"""
            <div style="margin-bottom:12px;">
                <a href="{url}" target="_blank" style="color:{color}; font-weight:bold; font-size:16px; text-decoration:none;">
                    {headline}
                </a>
                <br><small><em>{source} | {pub_date} | Sentiment: <strong>{sentiment}</strong></em></small>
            </div>
        """, unsafe_allow_html=True)

    total = pos + neg + neu
    st.markdown("---")
    st.subheader("📊 Sentiment Summary")
    st.write(f"Positive: {pos} ({pos/total*100:.1f}%)")
    st.write(f"Negative: {neg} ({neg/total*100:.1f}%)")
    st.write(f"Neutral: {neu} ({neu/total*100:.1f}%)")

# Hide Streamlit footer for clean UI
hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
