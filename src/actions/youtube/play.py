from pyyoutube import Client


class PlayYoutube():
    def __init__(self, api_key):
        self.client = Client(api_key=api_key)

    def search(self, query):
        res = self.client.search.list(q=query, parts=["snippet"], type=[
            "video"], maxResults=4)

        titles = []
        for item in res.items:
            titles.append(item.snippet.title)

        return '\n'.join(titles)
