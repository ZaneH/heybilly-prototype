import random
import giphy_client


class Giphy():
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query):
        api_instance = giphy_client.DefaultApi()

        try:
            api_response = api_instance.gifs_search_get(
                self.api_key, query, limit=10)
            return random.choice(api_response.data).images.original.url
        except Exception as e:
            print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)
            return None
