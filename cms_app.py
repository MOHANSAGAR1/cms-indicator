import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="CMS - Indian Market Sentiment", layout="wide", initial_sidebar_state='expanded')

# --- Sidebar setup ---
st.sidebar.title("CMS Setup")

newsapi_key = st.sidebar.text_input("Enter NewsAPI.org API Key:", type="password")

indices = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
}

timeframes = {
    "1 Day": "1d",
    "5 Days": "5d",
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
}

chart_types = ["Candlestick", "Line", "OHLC"]

selected_index = st.sidebar.selectbox("Select Index:", list(indices.keys()))
selected_timeframe = st.sidebar.selectbox("Select Timeframe:", list(timeframes.keys()))
selected_chart_type = st.sidebar.selectbox("Chart Type:", chart_types)
dark_mode = st.sidebar.checkbox("Dark Mode", value=False)

ticker = indices[selected_index]
period = timeframes[selected_timeframe]

# --- Styling for dark mode ---
if dark_mode:
    bg_color = "#0e1117"
    font_color = "white"
    template = "plotly_dark"
else:
    bg_color = "white"
    font_color = "black"
    template = "plotly_white"

st.markdown(
    f"""
    <style>
    .main {{
        background-color: {bg_color};
        color: {font_color};
    }}
    a {{
        color: #1f77b4;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Fetch price data ---
@st.cache_data(ttl=300)
def fetch_price_data(ticker_symbol, period):
    df = yf.download(ticker_symbol, period=period, progress=False, auto_adjust=True)
    return df

price_df = fetch_price_data(ticker, period)

if price_df.empty:
    st.error("No price data available.")
else:
    price_df.reset_index(inplace=True)

    # --- Plot price chart ---
    fig = go.Figure()
    if selected_chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=price_df['Date'], open=price_df['Open'], high=price_df['High'],
            low=price_df['Low'], close=price_df['Close'], name='Candlestick'
        ))
    elif selected_chart_type == "OHLC":
        fig.add_trace(go.Ohlc(
            x=price_df['Date'], open=price_df['Open'], high=price_df['High'],
            low=price_df['Low'], close=price_df['Close'], name='OHLC'
        ))
    else:  # Line chart
        fig.add_trace(go.Scatter(
            x=price_df['Date'], y=price_df['Close'], mode='lines', name='Close Price'
        ))

    fig.update_layout(
        title=f"{selected_index} Price Chart ({selected_timeframe})",
        xaxis_title="Date",
        yaxis_title="Price (INR)",
        template=template,
        height=500,
        xaxis_rangeslider_visible=False
    )

# --- Fetch news + sentiment ---
@st.cache_data(ttl=300)
def get_news_sentiment(api_key, query, from_date, to_date, page_size=30):
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}&from={from_date}&to={to_date}&language=en&"
        f"sortBy=publishedAt&pageSize={page_size}&apiKey={api_key}"
    )
    res = requests.get(url)
    data = res.json()
    articles = []
    if data.get("status") == "ok":
        for a in data.get("articles", []):
            title = a.get("title", "")
            desc = a.get("description", "")
            source = a.get("source", {}).get("name", "")
            url = a.get("url", "")
            pub = a.get("publishedAt", "")
            polarity = TextBlob(title + " " + (desc or "")).sentiment.polarity
            sentiment = "Neutral"
            if polarity > 0.1:
                sentiment = "Positive"
            elif polarity < -0.1:
                sentiment = "Negative"
            articles.append({
                "title": title,
                "description": desc,
                "source": source,
                "url": url,
                "published_at": pub,
                "sentiment": sentiment,
                "polarity": polarity,
            })
    return articles

if newsapi_key:
    to_date = datetime.utcnow().date()
    from_date = to_date - timedelta(days=3)
    articles = get_news_sentiment(newsapi_key, selected_index, from_date, to_date)

    # Sentiment summary
    pos = sum(1 for a in articles if a['sentiment'] == 'Positive')
    neg = sum(1 for a in articles if a['sentiment'] == 'Negative')
    neu = sum(1 for a in articles if a['sentiment'] == 'Neutral')
    total = len(articles)
    pos_pct = pos / total * 100 if total else 0
    neg_pct = neg / total * 100 if total else 0
    neu_pct = neu / total * 100 if total else 0

    # --- Display metrics ---
    st.markdown(f"## CMS Sentiment Indicator for **{selected_index}**")
    st.metric("Positive Sentiment", f"{pos} articles ({pos_pct:.1f}%)")
    st.metric("Negative Sentiment", f"{neg} articles ({neg_pct:.1f}%)")
    st.metric("Neutral Sentiment", f"{neu} articles ({neu_pct:.1f}%)")

    # --- Word Cloud for Sentiment Keywords ---
    combined_text = " ".join([a['title'] + " " + (a['description'] or "") for a in articles])
    if combined_text.strip():
        wordcloud = WordCloud(
            width=400, height=200,
            background_color='black' if dark_mode else 'white',
            colormap='RdYlGn'
        ).generate(combined_text)

        fig_wc, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig_wc)
else:
    st.warning("Enter your NewsAPI.org API key in the sidebar to view live news and sentiment.")

# --- Layout ---
col1, col2 = st.columns([3, 2])

with col1:
    if not price_df.empty:
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"Latest News for {selected_index}")
    if newsapi_key and articles:
        # Simple source logo mapping, extend as needed
        logo_map = {
            "Reuters": "https://s3.reutersmedia.net/resources_v2/images/favicon/favicon.ico",
            "Bloomberg": "https://assets.bwbx.io/s3/javelin/public/assets/images/favicon.ico",
            "CNBC": "https://www.cnbc.com/favicon.ico",
            "Forex Factory": "https://cdn.forexfactory.net/images/favicon.ico",
            # Add more logos here
        }

        for art in articles:
            color = {"Positive": "green", "Negative": "red", "Neutral": "gray"}.get(art['sentiment'], "black")
            logo_url = logo_map.get(art['source'], "")
            logo_html = f'<img src="{logo_url}" width="20" height="20" style="vertical-align:middle;margin-right:5px;">' if logo_url else ""
            st.markdown(f"{logo_html} <a href='{art['url']}' target='_blank'><b style='color:{color}'>{art['title']}</b></a>", unsafe_allow_html=True)
            st.markdown(f"<small><i>{art['source']} | {art['published_at'][:10]}</i></small>", unsafe_allow_html=True)
            st.markdown("---")
    elif newsapi_key:
        st.info("No recent news found.")
    else:
        st.info("Enter your NewsAPI key in the sidebar to load news.")

