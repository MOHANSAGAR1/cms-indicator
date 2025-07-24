import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
from datetime import datetime, timedelta

# Streamlit layout settings
st.set_page_config(
    page_title="CMS • Crowd Market Sentiment",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header
st.markdown("""
    <div style="background-color:#205072;padding:10px;border-radius:5px">
        <h1 style="color:#fff;text-align:center;">CMS • Crowd Market Sentiment</h1>
        <p style="color:#eee;text-align:center;font-size:1.1em;">
            Real-time Indian Market Sentiment & Index Tracker
        </p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar inputs
st.sidebar.header("🔍 Setup CMS")
try:
    api_key = st.secrets["NEWSAPI_KEY"]
except:
    api_key = st.sidebar.text_input("🔑 Enter NewsAPI Key", type="password")

)
indices = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "Nifty Midcap 50": "^MIDCAP50",
    "Nifty Smallcap 50": "^SMALLCAP50"
}
selected_index = st.sidebar.selectbox("Select Market Index:", list(indices.keys()))
ticker_symbol = indices[selected_index]
refresh_sec = st.sidebar.slider("Refresh Interval (sec)", 30, 600, 120)

# Helper functions
@st.cache_data(ttl=300)
def fetch_news():
    url = (
        f"https://newsapi.org/v2/everything?q=India stock market OR {selected_index}"
        f"&from={(datetime.now()-timedelta(days=1)).date()}&sortBy=publishedAt"
        f"&language=en&apiKey={api_key}"
    )
    res = requests.get(url).json()
    return res.get("articles", []) if res.get("status") == "ok" else []

def sentiment_score(text):
    return TextBlob(text).sentiment.polarity

# Main content area
if api_key:
    # --- Market Data ---
    st.subheader(f"{selected_index} • Real-Time Market Data")
    df_price = yf.download(ticker_symbol, period="5d", interval="1d")
    st.dataframe(df_price, use_container_width=True)

    # --- News & Sentiment ---
    articles = fetch_news()
    titles = [a["title"] for a in articles if a.get("title")]
    avg_sentiment = pd.Series([sentiment_score(t) for t in titles]).mean() if titles else 0
    status = (
        "🟢 Positive" if avg_sentiment > 0.1 else
        "🔴 Negative" if avg_sentiment < -0.1 else
        "🟡 Neutral"
    )

    st.markdown("### 📰 Market Sentiment Indicator")
    colA, colB = st.columns([1, 2])

    with colA:
        st.metric(label="Average Sentiment Score", value=f"{avg_sentiment:.2f}", delta=status)

    with colB:
        if titles:
            wc_text = " ".join(titles)
            wc = WordCloud(width=600, height=300, background_color="white").generate(wc_text)
            plt.figure(figsize=(6,3))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            st.pyplot(plt)

    # --- Latest News ---
    if titles:
        st.markdown("### 🆕 Latest News Headlines")
        for art in articles[:10]:
            st.markdown(f"**{art['title']}**")
            st.markdown(f"*{art['source']['name']} — {art['publishedAt'][:10]}*")
            st.markdown(f"{art.get('description','')}")
            st.markdown(f"[Read More]({art['url']})\n---")
    else:
        st.warning("No recent news found.")

    # Auto-refresh
    st.experimental_rerun()
else:
    st.warning("🔐 Please enter your NewsAPI key in the sidebar to start.")
