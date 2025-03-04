import logging

import tweepy
from tweepy.errors import TooManyRequests, HTTPException, BadRequest

class TwitterDriver:
    def __init__(self,
                 bearer_token: str,
                 api_key: str,
                 api_secret: str,
                 access_token: str,
                 access_secret: str):

        # Use Client for API v2 (for read-only tasks like getting retwiters)
        self.client = tweepy.Client(bearer_token=bearer_token,
                                    consumer_key=api_key, consumer_secret=api_secret,
                                    access_token=access_token, access_token_secret=access_secret)

    def get_retwitters_by_post_id(self, post_id):
        if not self.client:
            raise ValueError("Bearer Token is required for API v2 calls.")
        users = []
        try:
            retwiters = self.client.get_retweeters(id=post_id).data
            for user in retwiters:
                users.append(user.get('id'))
        except TooManyRequests:
            logging.error("Too many requests to twitter API")
        return users

    def twitt_post(self, text):
        try:
            response = self.client.create_tweet(text=text)
        except (TooManyRequests, BadRequest, HTTPException) as e:
            logging.error(f"API error: {e}")
            return None
        return response


if __name__ == '__main__':
    API_KEY = "4c0g8A3K3zu6p1ZZSuMofLPGW"
    API_SECRET = "r14hJ1WmWlYpUxxCyfOwdfy0bXG4azXs73kIkS0pP8Phs2Aoru"
    ACCESS_TOKEN = "1749834535653523456-O6z5Kywgg3q9f310U3EnAXlpmbXZzf"
    ACCESS_SECRET = "g8vYlKh74EnCFl6XaizK93ZWYqFXhBLh7LhwW6KmCrbiT"
    twitor = TwitterDriver(
        bearer_token="AAAAAAAAAAAAAAAAAAAAACdiygEAAAAAvLOl5G0WmWBwSOlBd%2FZmKL31sqE%3DWgf1JEOdp7cGOeCdVSnmMhF0khvrrbx4OV3lrSV4tYxn4pZx65",
        api_key=API_KEY, api_secret=API_SECRET,
        access_token=ACCESS_TOKEN, access_secret=ACCESS_SECRET
        )
    twitor.twitt_post(text="test_text")
    "1886409054647427325"
    "https://x.com/GShimko38911/status/1886409054647427325"