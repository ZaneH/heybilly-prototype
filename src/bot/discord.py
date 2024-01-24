import asyncio
import discord
import yt_dlp as youtube_dl


class BillyBot(discord.Bot):
    intents = discord.Intents.default()

    def __init__(self, queue: asyncio.Queue) -> None:
        super().__init__()
        self.queue = queue
        self.ready_event = asyncio.Event()

    async def start_processor_task(self):
        await self.ready_event.wait()
        while True:
            item = await self.queue.get()
            if item is None:
                continue

            if item["type"] == "youtube":
                video_id = item["video_id"]
                await self.play_youtube(video_id)
            elif item["type"] == "discord_post":
                text = item["text"]
                await self.send_nsfw(text)

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        self.ready_event.set()

    async def send_nsfw(self, message):
        channel = self.get_channel(976623220759339058)
        await channel.send(message)

    async def play_youtube(self, video_id):
        print("Playing video: ", video_id)
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        source = await YTDLSource.from_url(f"https://www.youtube.com/watch?v={video_id}", loop=self.loop)
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
