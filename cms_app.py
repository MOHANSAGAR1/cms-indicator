import streamlit as st
import yfinance as yf
import feedparser
from textblob import TextBlob
import plotly.graph_objects as go

st.set_page_config(page_title="📊 Live Market Pulse", layout="wide")

# Map of indices
indices = {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "BANK NIFTY": "^NSEBANK"}

# Sentiment & headlines
def get_sentiment_score():
    feed = feedparser.parse("https://news.google.com/rss/search?q=nifty+market&hl=en-IN&gl=IN&ceid=IN:en")
    scores = {"positive": 0, "negative": 0, "neutral": 0}
    headlines = []
    for entry in feed.entries[:15]:
        blob = TextBlob(entry.title)
        p = blob.sentiment.polarity
        if p > 0.1: scores["positive"] += 1
        elif p < -0.1: scores["negative"] += 1
        else: scores["neutral"] += 1
    return scores, [e.title for e in feed.entries[:5]]

# Market data fetcher
@st.cache_data(ttl=600)
def get_index_data(symbol):
    df = yf.download(symbol, period="5d", interval="1h", auto_adjust=True)
    if df.empty: return None
    df["Change %"] = df["Close"].pct_change() * 100
    return df

# UI
st.title("📈 Live Market Pulse Indicator")
sel = st.selectbox("Select Market Index", list(indices.keys()))
df = get_index_data(indices[sel])

if df is not None:
    st.subheader(f"{sel} – Last 5 Days")
    fig = go.Figure(go.Scatter(x=df.index, y=df["Close"], name="Price"))
    st.plotly_chart(fig, use_container_width=True)
    st.metric("Latest Change %", f"{df['Change %'].iloc[-1]:.2f}%")
else:
    st.warning("Unable to fetch market data.")

st.markdown("---")
scores, headlines = get_sentiment_score()
total = sum(scores.values())
pulse = (scores["positive"] - scores["negative"]) / (total or 1)

st.subheader("🧠 Market Sentiment Pulse")
st.progress((pulse + 1) / 2)
st.text(f"Positive: {scores['positive']}  Negative: {scores['negative']}  Neutral: {scores['neutral']}")

st.subheader("📰 Top Headlines")
for h in headlines:
    st.markdown(f"- {h}")
