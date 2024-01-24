import wolframalpha


class WolframAnswer():
    def __init__(self, app_id):
        self.client = wolframalpha.Client(app_id)

    def process(self, query):
        res = self.client.query(query)
        return next(res.results).text
