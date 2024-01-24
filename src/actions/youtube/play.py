import random
from pyyoutube import Client


class PlayYoutube():
    def __init__(self, api_key):
        self.client = Client(api_key=api_key)

    def search(self, query, shuffle=False) -> str:
        res = self.client.search.list(q=query, parts=["snippet"], type=[
            "video"], maxResults=10, order="relevance", safeSearch="none")

        if shuffle:
            choice = self._pick_random_video(res.items)
            return choice.id.videoId

        print("No shuffle")
        return res.items[0].id.videoId

    def _pick_random_video(self, videos):
        return random.choice(videos)
