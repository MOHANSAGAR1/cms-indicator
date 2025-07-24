import streamlit as st
import requests
import yfinance as yf
import plotly.graph_objects as go
from textblob import TextBlob

# ----------- Secure API Key Handling -----------
# Try to load API key from Streamlit secrets.toml or Cloud secrets
try:
    api_key = st.secrets["NEWSAPI"]["key"]
except Exception:
    # Fallback: ask user in sidebar (only if secret not set)
    api_key = st.sidebar.text_input("Enter your NewsAPI.org API Key:", type="password")

if not api_key:
    st.warning("🔐 Please enter your NewsAPI key to continue.")
    st.stop()

# ----------- Sidebar Inputs -----------

st.sidebar.header("🔍 CMS - Market Sentiment")

# Choose Index (example Indian indices with Yahoo ticker symbols)
indices = {
    "NIFTY 50": "^NSEI",
    "BSE SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
    "NIFTY IT": "^CNXIT"
}

selected_index = st.sidebar.selectbox("Select Market Index:", list(indices.keys()))
ticker_symbol = indices[selected_index]

# Timeframe selection for charts
timeframe = st.sidebar.selectbox("Select timeframe for chart:", ["1d", "5d", "1mo", "3mo", "6mo"])

# ----------- Fetch Price Data -----------

@st.cache_data(ttl=300)
def get_price_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
        return df
    except Exception as e:
        st.error(f"Failed to fetch price data: {e}")
        return None

df_price = get_price_data(ticker_symbol, timeframe)

if df_price is None or df_price.empty:
    st.error("No price data found for selected index and timeframe.")
    st.stop()

# ----------- Display Candlestick Chart -----------

fig = go.Figure(data=[go.Candlestick(
    x=df_price.index,
    open=df_price['Open'],
    high=df_price['High'],
    low=df_price['Low'],
    close=df_price['Close'],
    increasing_line_color='green',
    decreasing_line_color='red'
)])

fig.update_layout(
    title=f"{selected_index} Price Chart ({timeframe})",
    xaxis_title="Date",
    yaxis_title="Price (INR)",
    xaxis_rangeslider_visible=False,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ----------- Fetch News and Sentiment -----------

@st.cache_data(ttl=300)
def get_news_and_sentiment(query, api_key, page_size=20):
    url = ("https://newsapi.org/v2/everything?"
           f"q={query}&"
           "language=en&"
           "sortBy=publishedAt&"
           f"pageSize={page_size}&"
           f"apiKey={api_key}")
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            st.error(f"News API error: {data.get('message')}")
            return []
        return data.get("articles", [])
    except Exception as e:
        st.error(f"Failed to fetch news: {e}")
        return []

articles = get_news_and_sentiment(selected_index, api_key)

if not articles:
    st.warning("No recent news found for the selected index.")
else:
    st.subheader("📰 Latest News & Sentiment")
    pos_count = 0
    neg_count = 0
    neu_count = 0

    for article in articles:
        headline = article['title']
        description = article.get('description', '')
        source = article.get('source', {}).get('name', 'Unknown')
        url = article.get('url')
        published_at = article.get('publishedAt', '')[:10]

        # Sentiment analysis on headline + description
        text = f"{headline}. {description}"
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        if polarity > 0.05:
            sentiment = "Positive"
            pos_count += 1
            color = "green"
        elif polarity < -0.05:
            sentiment = "Negative"
            neg_count += 1
            color = "red"
        else:
            sentiment = "Neutral"
            neu_count += 1
            color = "gray"

        # Display with colored headline and source badge
        st.markdown(f"""
            <div style="border-bottom:1px solid #ddd; margin-bottom:10px; padding-bottom:10px;">
                <h4 style="color:{color}; margin-bottom:5px;">
                    <a href="{url}" target="_blank" style="text-decoration:none; color:{color};">{headline}</a>
                </h4>
                <small><em>{source} | {published_at} | Sentiment: <strong>{sentiment}</strong></em></small>
            </div>
            """, unsafe_allow_html=True)

    # ----------- Show Sentiment Summary -----------

    total = pos_count + neg_count + neu_count
    if total > 0:
        st.markdown("---")
        st.subheader("📊 Sentiment Summary")
        st.write(f"Positive: {pos_count} ({pos_count/total*100:.1f}%)")
        st.write(f"Negative: {neg_count} ({neg_count/total*100:.1f}%)")
        st.write(f"Neutral: {neu_count} ({neu_count/total*100:.1f}%)")

# ----------- Footer -----------

st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
