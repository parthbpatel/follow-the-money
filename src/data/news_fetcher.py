import feedparser


class NewsFetcher:

    @staticmethod
    def get_reuters_news():

        feed_url = (
            "https://feeds.reuters.com/reuters/businessNews"
        )

        feed = feedparser.parse(feed_url)

        headlines = []

        for entry in feed.entries[:10]:
            headlines.append(entry.title)

        return headlines
