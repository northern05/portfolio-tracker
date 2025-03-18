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


def create_crypto_sentiment_chart(historical_prices, sentiment_data: dict = None):
    """
    Creates an interactive Plotly chart comparing historical crypto prices with ELFA sentiment analysis data.

    Parameters:
    - historical_prices (list of dict): [{"date": "2025-03-10", "price": 2000}, ...]
    - sentiment_data (dict): ELFA sentiment response with metrics.

    Returns:
    - A Plotly figure.
    """
    # Convert historical prices to DataFrame
    price_df = pd.DataFrame(historical_prices)
    price_df["date"] = pd.to_datetime(price_df["date"])

    if sentiment_data:
        # Extract sentiment data
        sentiment_df = pd.DataFrame(sentiment_data)

        # Convert timestamps to date
        sentiment_df["date"] = pd.to_datetime(sentiment_df["mentioned_at"]).dt.date

        # Calculate sentiment score based on post metrics
        sentiment_df["sentiment_score"] = (
            sentiment_df["metrics"].apply(lambda x: x["like_count"] * 0.4 +
                                                    x["reply_count"] * 0.2 +
                                                    x["repost_count"] * 0.3 +
                                                    x["view_count"] * 0.1)
        )

        # Aggregate sentiment scores per day
        sentiment_grouped = sentiment_df.groupby("date")["sentiment_score"].sum().reset_index()
        sentiment_grouped["date"] = pd.to_datetime(sentiment_grouped["date"])  # Convert to datetime

        # Merge price and sentiment data
        merged_df = pd.merge(price_df, sentiment_grouped, on="date", how="left").ffill()
    else:
        merged_df = price_df

        # Create Figure
    fig = go.Figure()

    # Add Price Line (Orange) - Left Y-axis
    fig.add_trace(go.Scatter(
        x=merged_df["date"], y=merged_df["price"],
        mode="lines", name="Price (USD)",
        line=dict(color="orange", width=2),
        yaxis="y1"
    ))

    # # Add Sentiment Score Line (Blue) - Right Y-axis
    # fig.add_trace(go.Scatter(
    #     x=merged_df["date"], y=merged_df["sentiment_score"],
    #     mode="lines", name="Sentiment Score",
    #     line=dict(color="cyan", width=2, dash="dot"),  # Dashed line for differentiation
    #     yaxis="y2"
    # ))

    # Layout Settings
    fig.update_layout(
        title="Crypto Price vs Sentiment Analysis",
        xaxis=dict(title="Date"),
        yaxis=dict(
            title=dict(text="Price (USD)", font=dict(color="orange")),  # ✅ Correct
            tickfont=dict(color="orange"),
            side="left"
        ),
        # yaxis2=dict(
        #     title=dict(text="Sentiment Score", font=dict(color="cyan")),  # ✅ Correct
        #     tickfont=dict(color="cyan"),
        #     overlaying="y",
        #     side="right"
        # ),
        template="plotly_dark",
        legend_title="Metrics"
    )

    # Convert figure to PNG
    img_bytes = io.BytesIO()
    fig.write_image(img_bytes, format="png")
    img_bytes.seek(0)
    return img_bytes
