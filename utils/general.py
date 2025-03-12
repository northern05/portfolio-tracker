import io
import uuid
import requests
import plotly.graph_objects as go
import pandas as pd
import numpy as np


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
    Creates an interactive Plotly chart comparing historical crypto prices with ELFA sentiment analysis data
    for the last 7 days.

    Parameters:
    - historical_prices (list of dict): [{"date": "2025-03-10", "price": 2000}, ...]
    - sentiment_data (dict): ELFA sentiment response with "sentiment_score" data.

    Returns:
    - BytesIO PNG image of the chart.
    """
    # Convert historical prices to DataFrame
    price_df = pd.DataFrame(historical_prices)
    price_df["date"] = pd.to_datetime(price_df["date"])

    # Extract sentiment data
    sentiment_list = sentiment_data["data"]
    sentiment_df = pd.DataFrame(sentiment_list)

    # Convert mentioned_at timestamp to date
    sentiment_df["date"] = pd.to_datetime(sentiment_df["mentioned_at"]).dt.date

    # Calculate Sentiment Score using weighted sum of engagement metrics
    sentiment_df["sentiment_score"] = sentiment_df["metrics"].apply(
        lambda x: (1.0 * x.get("like_count", 0)) +
                  (0.8 * x.get("reply_count", 0)) +
                  (1.2 * x.get("repost_count", 0)) +
                  (0.001 * x.get("view_count", 0))  # Low weight for views
    )

    # Aggregate sentiment per day
    sentiment_grouped = sentiment_df.groupby("date")["sentiment_score"].mean().reset_index()
    sentiment_grouped["date"] = pd.to_datetime(sentiment_grouped["date"])

    # Normalize sentiment to fit price scale
    if not sentiment_grouped.empty:
        sentiment_grouped["sentiment_score"] = np.interp(
            sentiment_grouped["sentiment_score"],
            (sentiment_grouped["sentiment_score"].min(), sentiment_grouped["sentiment_score"].max()),
            (price_df["price"].min(), price_df["price"].max())
        )

    # Merge price and sentiment data
    merged_df = pd.merge(price_df, sentiment_grouped, on="date", how="left").ffill()

    # Keep only the last 7 days
    merged_df = merged_df.sort_values("date").tail(7)

    # Create Figure
    fig = go.Figure()

    # Add Price Line (Yellow)
    fig.add_trace(go.Scatter(
        x=merged_df["date"], y=merged_df["price"],
        mode="lines", name="Price (USD)",
        line=dict(color="yellow", width=2)
    ))

    # Add Sentiment Score Line (Blue)
    fig.add_trace(go.Scatter(
        x=merged_df["date"], y=merged_df["sentiment_score"],
        mode="lines", name="Sentiment Score",
        line=dict(color="cyan", width=2, dash="dot")  # Dashed line for better distinction
    ))

    # Layout Settings
    fig.update_layout(
        title="Crypto Price vs Sentiment Analysis (Last 7 Days)",
        xaxis_title="Date",
        yaxis_title="Price (USD) / Sentiment Score (Scaled)",
        template="plotly_dark",
        legend_title="Metrics",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
    )

    # Save as PNG
    img_bytes = io.BytesIO()
    fig.write_image(img_bytes, format="png")
    img_bytes.seek(0)

    return img_bytes
