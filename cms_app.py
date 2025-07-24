import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Page config
st.set_page_config(page_title="CMS - Indian Market Sentiment", layout="wide", initial_sidebar_state="expanded")

# Sidebar inputs
st.sidebar.title("CMS Setup")

newsapi_key = st.sidebar.text_input("Enter NewsAPI.org API Key:", type="password")

indices = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Midcap 50": "^MIDCAP50",
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

# Styling for dark/light mode
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
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    a {{
        color: #1f77b4;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch price data with caching
@st.cache_data(ttl=300)
def fetch_price_data(ticker_symbol, period):
    df = yf.download(ticker_symbol, period=period, progress=False, auto_adjust=True)
    return df

price_df = fetch_price_data(ticker, period)

if price_df.empty:
    st.error("No price data available for selected index and timeframe.")
else:
    price_df.reset_index(inplace=True)

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
    else:
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

# Fetch news and perform sentiment analysis
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

    pos = sum(1 for a in articles if a['sentiment'] == 'Positive')
    neg = sum(1 for a in articles if a['sentiment'] == 'Negative')
    neu = sum(1 for a in articles if a['sentiment'] == 'Neutral')
    total = len(articles)
    pos_pct = pos / total * 100 if total else 0
    neg_pct = neg / total * 100 if total else 0
    neu_pct = neu / total * 100 if total else 0

    st.markdown(f"## CMS Sentiment Indicator for **{selected_index}**")
    cols = st.columns(3)
    cols[0].metric("Positive Sentiment", f"{pos} articles ({pos_pct:.1f}%)")
    cols[1].metric("Negative Sentiment", f"{neg} articles ({neg_pct:.1f}%)")
    cols[2].metric("Neutral Sentiment", f"{neu} articles ({neu_pct:.1f}%)")

    # Show news articles
    st.markdown("### Recent News Articles")

    sentiment_colors = {
        "Positive": "green",
        "Negative": "red",
        "Neutral": "gray"
    }

    for article in articles:
        color = sentiment_colors.get(article['sentiment'], 'black')
        # Get source domain to fetch logo from Clearbit
        source_domain = article['source'].replace(' ', '').lower() + ".com"
        source_logo_url = f"https://logo.clearbit.com/{source_domain}"
        st.markdown(
            f"""
            <div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                <img src="{source_logo_url}" alt="{article['source']}" width="20" style="vertical-align: middle; margin-right: 8px;">
                <a href="{article['url']}" target="_blank" style="color:{color}; font-weight:bold; font-size:16px;">{article['title']}</a>
                <p style="color:#666;">{article['description']}</p>
                <small style="color:#999;">Source: {article['source']} | Published: {article['published_at'][:10]}</small>
            </div>
            """, unsafe_allow_html=True
        )

else:
    st.warning("🔐 Please enter your NewsAPI key in the sidebar to fetch news and sentiment.")

# Show the price chart
if not price_df.empty:
    st.plotly_chart(fig, use_container_width=True)

# Word cloud from news titles + descriptions
if newsapi_key and articles:
    all_text = " ".join([a['title'] + " " + (a['description'] or '') for a in articles])
    if all_text.strip():
        wordcloud = WordCloud(width=800, height=400, background_color=bg_color).generate(all_text)
        plt.figure(figsize=(12,6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)
