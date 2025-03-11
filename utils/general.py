import io
import uuid
import requests
import plotly.graph_objects as go
import pandas as pd


def generate_session_id() -> str:
    return uuid.uuid4().hex


def check_users_retwitt():
    response = requests.post(url="https://api.agent.zpoken.dev/api/v1/general/check_retwitts")
    if response.status_code == 200:
        return {"ok": True}
    else:
        return {"ok": False}


def sell_tokens():
    response = requests.post(url="http://127.0.0.1:6010/api/v1/general/sell_tokens")
    if response.status_code == 200:
        return {"ok": True}
    else:
        return {"ok": False}


def log_agent_balance():
    response = requests.post(url="https://api.agent.zpoken.dev/api/v1/general/log_agent_balance")
    if response.status_code == 200:
        return {"ok": True}
    else:
        return {"ok": False}


def create_crypto_sentiment_chart(historical_prices, sentiment_data):
    """
    Creates an interactive Plotly chart comparing historical crypto prices with ELFA sentiment analysis data.

    Parameters:
    - historical_prices (list of dict): [{"date": "2025-03-10", "price": 2000}, ...]
    - sentiment_data (dict): ELFA sentiment response with "sentiment_score" data.

    Returns:
    - A Plotly figure.
    """
    # Convert historical prices to DataFrame
    price_df = pd.DataFrame(historical_prices)
    price_df["date"] = pd.to_datetime(price_df["date"])

    # Extract sentiment data
    sentiment_list = sentiment_data["data"]
    sentiment_df = pd.DataFrame(sentiment_list)

    # Convert mentioned_at timestamp to date
    sentiment_df["date"] = pd.to_datetime(sentiment_df["mentioned_at"]).dt.date

    # Aggregate sentiment metrics per day
    sentiment_df["engagement_score"] = (
        sentiment_df["metrics"].apply(
            lambda x: x["like_count"] + x["reply_count"] + x["repost_count"] + x["view_count"])
    )

    sentiment_grouped = sentiment_df.groupby("date")["engagement_score"].sum().reset_index()
    sentiment_grouped["date"] = pd.to_datetime(sentiment_grouped["date"])  # Convert to datetime

    # Merge price and sentiment data
    merged_df = pd.merge(price_df, sentiment_grouped, on="date", how="left").fillna(0)

    # Create Figure
    fig = go.Figure()

    # Add Price Line (Orange)
    fig.add_trace(go.Scatter(
        x=merged_df["date"], y=merged_df["price"],
        mode="lines", name="Price (USD)",
        line=dict(color="orange", width=2)
    ))

    # Add Sentiment Engagement (Blue Bars)
    fig.add_trace(go.Bar(
        x=merged_df["date"], y=merged_df["engagement_score"],
        name="Sentiment Engagement",
        marker_color="cyan", opacity=0.6
    ))

    # Layout Settings
    fig.update_layout(
        title="Crypto Price vs Social Media Sentiment Engagement",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        yaxis2=dict(
            title="Engagement Score",
            overlaying="y",
            side="right"
        ),
        template="plotly_dark",
        legend_title="Metrics"
    )

    img_bytes = io.BytesIO()
    fig.write_image(img_bytes, format="png")  # Save as PNG
    img_bytes.seek(0)
    return img_bytes
