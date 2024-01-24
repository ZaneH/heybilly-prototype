import asyncio
import discord
import yt_dlp as youtube_dl

from src.tts.streamlabs import StreamlabsTTS, StreamlabsVoice


class BillyBot(discord.Bot):
    voice = StreamlabsVoice.Ivy
    intents = discord.Intents.default()

    def __init__(self, queue: asyncio.Queue) -> None:
        super().__init__()
        self.queue = queue
        self.ready_event = asyncio.Event()

    async def start_processor_task(self):
        await self.ready_event.wait()
        while True:
            try:
                item = await self.queue.get()
                if item is None:
                    continue

                if item["type"] == "youtube":
                    stop = item.get("stop", False)
                    if stop:
                        self.safely_stop()
                        continue
                    else:
                        video_id = item["video_id"]
                        await self.play_youtube(video_id)
                if item["type"] == "sound_effect":
                    video_id = item["video_id"]
                    await self.play_youtube(video_id)
                elif item["type"] == "discord_post":
                    text = item.get("text", None)
                    image = item.get("image", None)
                    msg = ""

                    if text is not None:
                        msg += text

                    if image is not None:
                        msg += image

                    await self.send_nsfw(msg)
                elif item["type"] == "tts":
                    if getattr(self, "vc", None) is None:
                        print("Not in a voice channel.")
                        continue

                    text = item["text"]
                    mp3_url = StreamlabsTTS(self.voice).get_url(text)
                    if mp3_url is not None:
                        old_source = None
                        if self.vc.is_playing():
                            old_source = self.vc.source
                            self.vc.pause()

                        tts_source = await self.create_yt_audio_source(mp3_url)

                        def after_callback(error, old_source):
                            if error:
                                print(f'Player error: {error}')
                            elif old_source:
                                self.vc.play(old_source, after=lambda e: print(
                                    f'Player error: {e}') if e else None)

                        self.vc.play(
                            tts_source, after=lambda e: after_callback(e, old_source))
            except Exception as e:
                raise e

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        self.ready_event.set()

    async def send_nsfw(self, message, files=None):
        try:
            channel = self.get_channel(976623220759339058)
            await channel.send(message, files=files)
        except Exception as e:
            print("Error sending Discord message: ", e)

    def safely_stop(self):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        self.vc.stop()

    async def play_youtube(self, video_id):
        self.safely_stop()

        source = await YTDLSource.from_url(f"https://www.youtube.com/watch?v={video_id}", loop=self.loop, stream=True)
        self.vc.play(source, after=lambda e: print(
            'Player error: %s' % e) if e else None)

    async def create_yt_audio_source(self, url):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        source = await YTDLSource.from_url(url, loop=self.loop, stream=True)
        return source

    def play(self, source):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        self.vc.play(source, after=lambda e: print(
            'Player error: %s' % e) if e else None)


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
