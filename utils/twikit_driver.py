import json
import asyncio
from twikit import Client, TooManyRequests, UserNotFound, Unauthorized
from datetime import datetime, timedelta, timezone
from random import randint


class TwitterScraper:
    def __init__(self, username: str, email: str, password: str, min_tweets: int = 10):
        self.username = username
        self.email = email
        self.password = password
        self.min_tweets = min_tweets
        self.client = Client(language="en-US")
        self.login_state = False

    async def login(self):
        """Authenticate and store session cookies."""
        await self.client.login(auth_info_1=self.username, auth_info_2=self.email, password=self.password)
        self.client.save_cookies("cookies.json")
        self.client.load_cookies("cookies.json")

    async def get_tweets(self, user_id: str, tweets):
        """Retrieve tweets using Twikit."""
        if tweets is None:
            print(f"{datetime.now()} - Fetching initial tweets...")
            tweets = await self.client.get_user_tweets(user_id=user_id, tweet_type='Tweets', count=3)
        else:
            wait_time = randint(5, 10)
            print(f"{datetime.now()} - Fetching next tweets after {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            tweets = await tweets.next()

        return tweets

    async def get_user_id_by_username(self, username: str):
        user = await self.client.get_user_by_screen_name(screen_name=username)
        return user.id

    async def get_username_by_user_id(self, user_id: str):
        if not self.login_state:
            await self.login()
            self.login_state = True
        user = await self.client.get_user_by_id(user_id=user_id)
        return user.screen_name

    async def fetch_tweets(self, protocol_name: str):
        if not self.login_state:
            await self.login()
            self.login_state = True
        tweet_data = []
        tweets = None
        while True:
            try:
                user_id = await self.get_user_id_by_username(username=protocol_name)
                tweets = await self.get_tweets(tweets=tweets, user_id=user_id)
            except TooManyRequests as e:
                rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
                print(f"{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}")
                wait_time = (rate_limit_reset - datetime.now()).total_seconds()
                await asyncio.sleep(wait_time)
            except UserNotFound as e:
                print(f"{protocol_name} not exists.")

            except Unauthorized as e:
                await self.login()
                user_id = await self.get_user_id_by_username(username=protocol_name)
                tweets = await self.get_tweets(tweets=tweets, user_id=user_id)

            if not tweets and not tweet_data:
                print(f"{datetime.now()} - No more tweets found")
                return None

            last_tweet_date = None
            for tweet in tweets:
                last_tweet_date = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
                if last_tweet_date > (datetime.now(timezone.utc) - timedelta(days=7)):
                    tweet_data.append({"content": tweet.text,
                                       "created_at": tweet.created_at,
                                       "retweets": tweet.retweet_count,
                                       "likes": tweet.favorite_count})
            if last_tweet_date < (datetime.now(timezone.utc) - timedelta(days=1)): break

        return tweet_data


if __name__ == "__main__":
    async def run():
        urls = ["x.com/Bitcoin",
                "x.com/ethereum",
                "x.com/Tether_to",
                "x.com/ripple",
                "x.com/binance",
                "x.com/solana"]
        scraper = TwitterScraper(
            username="GShimko38911",
            email="glib@zpoken.io",
            password="y5iwbGq=/nX:'CL",
            min_tweets=10,
        )
        await scraper.setup()
        with open("data.txt", "a", encoding="utf-8") as file:
            for url in urls:
                protocol_name = url.split("/")[-1]
                results = await scraper.fetch_tweets(protocol_name=protocol_name)
                file.write(protocol_name + "\n")
                file.write("=" * 100 + "\n")
                file.write(json.dumps(results, indent=4, ensure_ascii=False))
                file.write("\n\n")
                print(results)
                await asyncio.sleep(5)


    asyncio.run(run())
