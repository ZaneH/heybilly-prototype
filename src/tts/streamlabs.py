import requests


class StreamlabsTTS():
    def __init__(self, voice):
        self.voice = voice

    def get_url(self, text):
        try:
            url = "https://streamlabs.com/polly/speak"
            payload = {
                "voice": self.voice,
                "text": text
            }

            res = requests.post(url, data=payload)
            return res.json()['speak_url']

        except Exception as e:
            print("Error getting Streamlabs TTS URL: ", e)
            return None
