import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from textblob import TextBlob

# ----- Configuration -----

st.set_page_config(page_title="CMS - Indian Market Sentiment", layout="wide")

# Indian market indices and their Yahoo ticker symbols
INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    # Remove if no data: "Midcap 50": "^MIDCAP50",
}

TIMEFRAMES = {
    "1 Day": "1d",
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
}

# --- Sidebar ---

st.sidebar.title("CMS Setup")

newsapi_key = st.sidebar.text_input(
    "Enter your NewsAPI.org API Key:", type="password"
)

selected_index_name = st.sidebar.selectbox("Select Index:", list(INDICES.keys()))
selected_index_ticker = INDICES[selected_index_name]

selected_timeframe_name = st.sidebar.selectbox("Select Timeframe:", list(TIMEFRAMES.keys()))
selected_timeframe = TIMEFRAMES[selected_timeframe_name]

# --- Fetch Price Data ---

@st.cache_data(ttl=300)
def get_price_data(ticker, period):
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    return df

price_data = get_price_data(selected_index_ticker, selected_timeframe)

if price_data.empty:
    st.error("No price data found for the selected index/timeframe.")
else:
    price_data.reset_index(inplace=True)

    # --- Plot Chart ---
    fig = go.Figure(data=[go.Candlestick(
        x=price_data['Date'],
        open=price_data['Open'],
        high=price_data['High'],
        low=price_data['Low'],
        close=price_data['Close'],
        name='Candlestick'
    )])

    fig.add_trace(go.Scatter(
        x=price_data['Date'],
        y=price_data['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='blue', width=1)
    ))

    fig.update_layout(
        title=f"{selected_index_name} Price Chart ({selected_timeframe_name})",
        xaxis_title='Date',
        yaxis_title='Price (INR)',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=500
    )

# --- Fetch News and Sentiment Analysis ---

@st.cache_data(ttl=300)
def fetch_news_and_sentiment(api_key, query, from_date, to_date, page_size=20):
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={from_date}&to={to_date}&"
        "language=en&"
        "sortBy=publishedAt&"
        f"pageSize={page_size}&"
        f"apiKey={api_key}"
    )
    response = requests.get(url)
    data = response.json()

    articles = []
    if data.get("status") == "ok":
        for article in data.get("articles", []):
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            source_name = article.get("source", {}).get("name", "")
            published_at = article.get("publishedAt", "")
            # Sentiment using TextBlob (simple polarity measure)
            sentiment_polarity = TextBlob(title + ". " + (description or "")).sentiment.polarity
            sentiment = "Neutral"
            if sentiment_polarity > 0.1:
                sentiment = "Positive"
            elif sentiment_polarity < -0.1:
                sentiment = "Negative"
            articles.append({
                "title": title,
                "description": description,
                "url": url,
                "source": source_name,
                "published_at": published_at,
                "sentiment": sentiment,
                "polarity": sentiment_polarity,
            })
    return articles

if newsapi_key:
    to_date = datetime.utcnow().date()
    from_date = to_date - timedelta(days=2)
    articles = fetch_news_and_sentiment(newsapi_key, selected_index_name, from_date, to_date)

    # --- Sentiment Summary ---
    pos = sum(1 for a in articles if a['sentiment'] == 'Positive')
    neg = sum(1 for a in articles if a['sentiment'] == 'Negative')
    neu = sum(1 for a in articles if a['sentiment'] == 'Neutral')
    total = len(articles)
    if total > 0:
        pos_pct = pos / total * 100
        neg_pct = neg / total * 100
        neu_pct = neu / total * 100
    else:
        pos_pct = neg_pct = neu_pct = 0

    st.markdown(f"### CMS Sentiment Indicator for **{selected_index_name}**")
    st.metric(label="Positive Sentiment", value=f"{pos} articles ({pos_pct:.1f}%)", delta=None)
    st.metric(label="Negative Sentiment", value=f"{neg} articles ({neg_pct:.1f}%)", delta=None)
    st.metric(label="Neutral Sentiment", value=f"{neu} articles ({neu_pct:.1f}%)", delta=None)

else:
    st.warning("Please enter your NewsAPI key in the sidebar to view live news and sentiment.")

# --- Layout: Show chart and news side by side ---

col1, col2 = st.columns([3, 2])

with col1:
    if not price_data.empty:
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"Latest News for {selected_index_name}")

    if newsapi_key and articles:
        for art in articles:
            # Color headlines by sentiment
            color = {
                "Positive": "green",
                "Negative": "red",
                "Neutral": "gray"
            }.get(art['sentiment'], "black")

            # Source logo example: You can create a mapping dict for known sources/logos or use favicon APIs
            # For simplicity, just showing source name here
            st.markdown(f"**[{art['title']}]({art['url']})**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:{color}'>{art['sentiment']}</span> | Source: {art['source']} | Published: {art['published_at'][:10]}", unsafe_allow_html=True)
            st.markdown("---")
    elif newsapi_key:
        st.info("No recent news articles found.")
    else:
        st.info("Enter your NewsAPI key to load news.")

# --- Footer or additional UI touches ---

st.markdown("""
<style>
    .css-18e3th9 { padding-top: 1rem; }
    .stMetric { margin-bottom: 15px !important; }
</style>
""", unsafe_allow_html=True)
