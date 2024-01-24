import argparse
import asyncio
import os
import re
from datetime import datetime, timedelta
from queue import Queue
from sys import platform
from time import sleep

import numpy as np
import speech_recognition as sr
import torch
import whisper
from src.bot.discord import BillyBot
from src.ai.response_author import ResponseAuthor

from src.ai.tool_picker import Tool, ToolPicker

WAKE_WORDS = ["okay billy", "hey billy"]


class Listen():
    def __init__(self, openai_client, wolfram_client, youtube_client, giphy_client) -> None:
        self.should_stop = False
        self.tool_picker = ToolPicker(openai_client)
        self.response_author = ResponseAuthor(openai_client)
        self.wolfram_client = wolfram_client
        self.youtube_client = youtube_client
        self.giphy_client = giphy_client

        self.data_queue = asyncio.Queue()

    def stop(self):
        self.should_stop = True

    async def process_audio_queue(self):
        while not self.should_stop:
            audio_data = await self.data_queue.get()  # Get data asynchronously

            # Convert in-ram buffer to something the model can use directly without needing a temp file.
            # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
            # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
            audio_np = np.frombuffer(
                audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Read the transcription.
            result = await asyncio.to_thread(
                self.audio_model.transcribe,
                audio_np,
                fp16=torch.cuda.is_available()
            )
            text = result['text'].strip()

            # Process the transcript (this could be another async method if more complex processing is needed)
            await self.process_transcript(text)

            await asyncio.sleep(0.25)  # Non-blocking sleep

    async def start(self, text_queue: asyncio.Queue):
        self.text_queue = text_queue
        self.audio_queue = asyncio.Queue()

        parser = argparse.ArgumentParser()
        parser.add_argument("--model", default="medium", help="Model to use",
                            choices=["tiny", "base", "small", "medium", "large"])
        parser.add_argument("--non_english", action='store_true',
                            help="Don't use the english model.")
        parser.add_argument("--energy_threshold", default=1000,
                            help="Energy level for mic to detect.", type=int)
        parser.add_argument("--record_timeout", default=2,
                            help="How real time the recording is in seconds.", type=float)
        parser.add_argument("--phrase_timeout", default=3,
                            help="How much empty space between recordings before we "
                            "consider it a new line in the transcription.", type=float)
        if 'linux' in platform:
            parser.add_argument("--default_microphone", default='pulse',
                                help="Default microphone name for SpeechRecognition. "
                                "Run this with 'list' to view available Microphones.", type=str)
        args = parser.parse_args()

        # The last time a recording was retrieved from the queue.
        phrase_time = None
        # Thread safe Queue for passing data from the threaded recording callback.
        data_queue = asyncio.Queue()
        # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
        recorder = sr.Recognizer()
        recorder.energy_threshold = args.energy_threshold
        # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
        recorder.dynamic_energy_threshold = False

        # Important for linux users.
        # Prevents permanent application hang and crash by using the wrong Microphone
        if 'linux' in platform:
            mic_name = args.default_microphone
            if not mic_name or mic_name == 'list':
                print("Available microphone devices are: ")
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"{index}. \"{name}\"")
                return
            else:
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    if mic_name in name:
                        source = sr.Microphone(
                            sample_rate=16000, device_index=index)
                        break
        else:
            # print device index and name
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"{index}. \"{name}\"")

            device_index = int(input("Enter Microphone device index: "))
            source = sr.Microphone(device_index, sample_rate=16000)

        # Load / Download model
        model = args.model
        if args.model != "large" and not args.non_english:
            model = model + ".en"
        self.audio_model = whisper.load_model(model)

        record_timeout = args.record_timeout
        phrase_timeout = args.phrase_timeout

        transcription = ['']

        with source:
            recorder.adjust_for_ambient_noise(source)

        loop = asyncio.get_running_loop()

        def record_callback(_, audio: sr.AudioData) -> None:
            """
            Threaded callback function to receive audio data when recordings finish.
            audio: An AudioData containing the recorded bytes.
            """
            # This function will be called from a background thread
            data = audio.get_raw_data()

            # Schedule the data to be put into the queue in the thread-safe manner
            loop.call_soon_threadsafe(self.data_queue.put_nowait, data)

        # Create a background thread that will pass us raw audio bytes.
        # We could do this manually but SpeechRecognizer provides a nice helper.
        recorder.listen_in_background(
            source, record_callback, phrase_time_limit=record_timeout
        )

        # Cue the user that we're ready to go.
        print("Billy is listening...\n")

        await self.process_audio_queue()

    def has_wake_word(self, line):
        line = line.lower()
        alpha_regex = re.compile('[^a-zA-Z ]')
        line = alpha_regex.sub('', line)

        for word in WAKE_WORDS:
            if word in line:
                return True

        return False

    async def process_transcript(self, line):
        if not self.has_wake_word(line):
            return

        print("*" * 80)
        print("* ", line)
        print("*" * 80)

        # TOOL TREE
        data = self.tool_picker.determine_tools_and_query(line)
        tool = data.get('tool', Tool.NoTool)
        query = data.get('query', None)
        text = data.get('text', None)

        print(tool, query, text)

        text_response = None
        if tool == Tool.NoTool:
            text_response = self.response_author.write_response(line)
        elif tool == Tool.WolframAlpha:
            added_info = self.wolfram_client.process(query)
            text_response = self.response_author.write_response(
                line, added_info)
        elif tool == Tool.YouTube:
            random_video_id = self.youtube_client.search(query)
            await self.text_queue.put({
                "type": "youtube",
                "video_id": random_video_id
            })
        elif tool == Tool.SoundEffect:
            random_video_id = self.youtube_client.search(query)
            await self.text_queue.put({
                "type": "sound_effect",
                "video_id": random_video_id
            })
        elif tool == Tool.DiscordPost:
            if text is not None:
                await self.text_queue.put({
                    "type": "discord_post",
                    "text": query
                })
            elif query is not None:
                image_url = self.giphy_client.search(query)
                await self.text_queue.put({
                    "type": "discord_post",
                    "image": image_url
                })
        else:
            print("Unknown tool", tool)

        if text_response is not None:
            return await self.text_queue.put({
                "type": "tts",
                "text": text_response
            })
