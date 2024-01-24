import requests
from enum import Enum


class StreamlabsVoice(Enum):
    Nicole = 0
    Mia = 1
    Matthew = 2
    Brian = 3
    Ivy = 23
    Kimberly = 24
    Chantal = 25
    Amy = 26
    Vicki = 27
    Marlene = 28
    Karl = 31
    Zeina = 32
    Miguel = 33
    Mathieu = 34
    Justin = 35
    Lucia = 36
    Jacek = 37
    Salli = 52
    Aditi = 53
    Vitoria = 54
    Emma = 55
    Hans = 56
    Kendra = 57


class StreamlabsTTS():
    def __init__(self, voice=StreamlabsVoice.Ivy):
        self.voice = voice

    def get_url(self, text):
        if text is None:
            return None

        try:
            url = "https://streamlabs.com/polly/speak"
            payload = {
                "voice": self.voice.name,
                "text": text
            }

            res = requests.post(url, data=payload)
            return res.json()['speak_url']

        except Exception as e:
            print("Error getting Streamlabs TTS URL: ", e)
            return None
