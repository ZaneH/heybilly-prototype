import asyncio
import re
from datetime import datetime, timedelta

import numpy as np
import speech_recognition as sr
import torch
import whisper

from src.ai.tool_picker import Tool

# Heavily based on davabase/whisper_real_time for real time transcription
# https://github.com/davabase/whisper_real_time/tree/master

WAKE_WORDS = ["ok billy", "yo billy", "okay billy", "hey billy"]


class Listen():
    def __init__(self, tool_picker, response_author, wolfram_client, youtube_client, giphy_client) -> None:
        self.should_stop = False
        self.tool_picker = tool_picker
        self.response_author = response_author
        self.wolfram_client = wolfram_client
        self.youtube_client = youtube_client
        self.giphy_client = giphy_client

        self.data_queue = asyncio.Queue()

    def stop(self):
        self.should_stop = True

    async def process_audio_queue(self, phrase_timeout: float):
        now = datetime.utcnow()
        transcription = ['']
        # The last time a recording was retrieved from the queue.
        phrase_time = None
        while not self.should_stop:
            phrase_complete = False
            # If enough time has passed between recordings, consider the phrase complete.
            # Clear the current working audio buffer to start over with the new data.
            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                phrase_complete = True
            # This is the last time we received new audio data from the queue.
            phrase_time = now

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
            if phrase_complete:
                transcription.append(text)
            else:
                transcription[-1] = text

            # Process transcript in the background.
            await self.process_transcript(transcription[-1])

            await asyncio.sleep(0.25)  # Non-blocking sleep

    async def start(self, action_queue: asyncio.Queue):
        self.action_queue = action_queue
        self.audio_queue = asyncio.Queue()
        non_english = False

        # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
        recorder = sr.Recognizer()
        recorder.energy_threshold = 1000
        # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
        recorder.dynamic_energy_threshold = False

        # print device index and name
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"{index}. \"{name}\"")

        device_index = int(input("Enter Microphone device index: "))
        source = sr.Microphone(device_index, sample_rate=16000)

        # Load / Download model
        model = "medium"
        if model != "large" and not non_english:
            model = model + ".en"
        self.audio_model = whisper.load_model(model)

        # These could be fine-tuned. I'm not sure what the best values are.
        record_timeout = 6
        phrase_timeout = 3

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

        await self.process_audio_queue(phrase_timeout)

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

        await self.run_tool_tree(line)

    async def run_tool_tree(self, line):
        data = self.tool_picker.determine_tools_and_query(line)
        tool = data.get('tool', Tool.NoTool)
        query = data.get('query', None)
        text = data.get('text', None)
        stop = data.get('stop', 0)
        play = data.get('play', 0)
        pause = data.get('pause', 0)
        shuffle = data.get('shuffle', 0)

        # debug detected flags of the tool picker
        print(tool, query, text, stop, play, pause, shuffle)

        text_response = None
        if tool == Tool.NoTool:
            text_response = self.response_author.write_response(line)
        elif tool == Tool.WolframAlpha:
            added_info = self.wolfram_client.process(query)
            text_response = self.response_author.write_response(
                line, added_info)
        elif tool == Tool.YouTube:
            # youtube controls
            if stop or play or pause:
                await self.action_queue.put({
                    "type": "youtube",
                    "stop": stop,
                    "play": play,
                    "pause": pause
                })

            else:
                if query is None:
                    text_response = "I didn't hear your YouTube search"
                else:
                    # search for specific song or shuffle
                    video_res = self.youtube_client.search(query, shuffle)
                    video_id = video_res.id.videoId

                    await self.action_queue.put({
                        "type": "youtube",
                        "video_id": video_id
                    })
        elif tool == Tool.SoundEffect:
            # shuffle for a sfx
            video_res = self.youtube_client.search(query, True)
            random_video_id = video_res.id.videoId

            await self.action_queue.put({
                "type": "sound_effect",
                "video_id": random_video_id
            })
        elif tool == Tool.DiscordPost:
            # if a search query is provided, find a gif
            image_url = None
            if query is not None:
                image_url = self.giphy_client.search(query)

            await self.action_queue.put({
                "type": "discord_post",
                "image": image_url,
                "text": text
            })
        else:
            print("Unknown tool", tool)

        if text_response is not None:
            return await self.action_queue.put({
                "type": "tts",
                "text": text_response
            })
