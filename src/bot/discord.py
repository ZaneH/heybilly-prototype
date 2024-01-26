import asyncio
import discord
import yt_dlp as youtube_dl

from src.tts.streamlabs import StreamlabsTTS, StreamlabsVoice


class BillyBot(discord.Bot):
    voice = StreamlabsVoice.Ivy
    intents = discord.Intents.default()

    def __init__(self, queue: asyncio.Queue, discord_channel_id: int) -> None:
        super().__init__()
        self.queue = queue
        self.ready_event = asyncio.Event()
        self.discord_channel_id = discord_channel_id

        @self.slash_command(name="connect", description="Add Billy to the conversation.")
        async def connect(ctx: discord.context.ApplicationContext):
            if ctx.user.voice is None:
                await ctx.respond("You are not in a voice channel.", ephemeral=True)
                return

            self.vc = await ctx.user.voice.channel.connect()
            return await ctx.respond("Joining voice channel.", ephemeral=True)

        @self.slash_command(name="kick", description="Kick Billy from your voice channel.")
        async def kick(ctx: discord.context.ApplicationContext):
            try:
                if getattr(self, "vc", None):
                    await ctx.respond("Not in a voice channel.", ephemeral=True)
                    self.vc = self.voice_clients[0]

                await self.vc.disconnect()
                self.vc = None
                return await ctx.respond("Leaving voice channel.", ephemeral=True)
            except Exception as e:
                return await ctx.respond(f"Couldn't kick the bot.", ephemeral=True)

        @self.slash_command(name="stop", description="Stop playing audio.")
        async def stop(ctx: discord.context.ApplicationContext):
            self.safely_stop()
            return await ctx.respond("Stopping audio.", ephemeral=True)

        @self.slash_command(name="voice", description="Set the TTS voice.")
        async def set_voice(ctx: discord.context.ApplicationContext, voice: StreamlabsVoice):
            self.voice = voice
            return await ctx.respond(f"Set voice to {voice}.", ephemeral=True)

    async def _handle_youtube_item(self, item) -> bool:
        stop = item.get("stop", 0)
        play = item.get("play", 0)
        pause = item.get("pause", 0)

        if stop:
            self.safely_stop()
        elif pause:
            self.safely_pause()
        elif play:
            self.safely_resume()
        else:
            video_id = item["video_id"]
            await self.play_youtube(video_id)

    async def start_processor_task(self):
        await self.ready_event.wait()
        while True:
            try:
                item = await self.queue.get()
                if item is None:
                    continue

                if item["type"] == "youtube":
                    if await self._handle_youtube_item(item):
                        continue
                if item["type"] == "sound_effect":
                    video_id = item["video_id"]
                    source = await self.create_yt_audio_source(
                        f"https://www.youtube.com/watch?v={video_id}")
                    self._play_and_restore(source, 5)
                elif item["type"] == "discord_post":
                    text = item.get("text", None)
                    image = item.get("image", None)
                    msg = ""

                    if text is not None:
                        msg += text

                    if image is not None:
                        if msg != "":
                            msg += "\n"

                        msg += image

                    await self.send_channel_message(msg)
                elif item["type"] == "discord_post.youtube":
                    text = item.get("text", None)
                    if text is not None:
                        await self.send_channel_message(text)

                elif item["type"] == "tts":
                    if getattr(self, "vc", None) is None:
                        print("Not in a voice channel.")
                        continue

                    text = item["text"]
                    mp3_url = StreamlabsTTS(self.voice).get_url(text)
                    if mp3_url is not None:
                        tts_source = await self.create_yt_audio_source(mp3_url)
                        self._play_and_restore(tts_source)

            except Exception as e:
                raise e

    def _play_and_restore(self, new_source, max_duration=0):
        def after_callback(error, old_source, timeout_task):
            if error:
                print(f'Player error: {error}')
            elif old_source:
                self.vc.play(old_source, after=lambda e: print(
                    f'Player error: {e}') if e else None)

            if timeout_task and not timeout_task.done():
                timeout_task.cancel()

        async def stop_playback_after_timeout(duration):
            await asyncio.sleep(duration)
            self.safely_stop()

        old_source = None
        if self.vc.is_playing():
            old_source = self.vc.source
            self.vc.pause()

        timeout_task = None
        self.vc.play(new_source, after=lambda e: after_callback(
            e, old_source, timeout_task))

        if max_duration > 0:
            timeout_task = asyncio.create_task(
                stop_playback_after_timeout(max_duration))

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        self.ready_event.set()

    async def send_channel_message(self, message, files=None):
        try:
            channel = self.get_channel(self.discord_channel_id)
            await channel.send(message, files=files)
        except Exception as e:
            print("Error sending Discord message: ", e)

    def safely_stop(self):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        if self.vc.is_playing():
            self.vc.stop()

    def safely_pause(self):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        if self.vc.is_playing():
            self.vc.pause()

    def safely_resume(self):
        if getattr(self, "vc", None) is None:
            print("Not in a voice channel.")
            return

        if self.vc.is_paused():
            self.vc.resume()

    async def play_youtube(self, video_id):
        try:
            if getattr(self, "vc", None) is None:
                print("Not in a voice channel.")
                return

            self.safely_stop()

            source = await YTDLSource.from_url(f"https://www.youtube.com/watch?v={video_id}", loop=self.loop, stream=True)
            self.vc.play(source, after=lambda e: print(
                'Player error: %s' % e) if e else None)
        except Exception as e:
            print("Error playing YouTube video: ", e)

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
    'before_options':
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
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
