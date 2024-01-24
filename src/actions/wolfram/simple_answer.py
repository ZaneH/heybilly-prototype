import wolframalpha


class WolframAnswer():
    def __init__(self, app_id):
        self.client = wolframalpha.Client(app_id)

    def process(self, query):
        try:
            res = self.client.query(query)
            return next(res.results).text
        except Exception as e:
            print(f"Error getting WolframAlpha result: {e}, {query}")
            return None
