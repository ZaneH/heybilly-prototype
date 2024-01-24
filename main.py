import asyncio
import os

import discord
from dotenv import load_dotenv
from openai import OpenAI

from src.actions.images.giphy import Giphy
from src.actions.wolfram.simple_answer import WolframAnswer
from src.actions.youtube.play import PlayYoutube
from src.bot.discord import BillyBot
from src.tts.streamlabs import StreamlabsVoice
from src.voice.listen import Listen

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

youtube = PlayYoutube(GOOGLE_API_KEY)
wolfram = WolframAnswer(WOLFRAM_APP_ID)
giphy = Giphy(GIPHY_API_KEY)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

loop = asyncio.get_event_loop()


async def discord_bot_task(bot: BillyBot):
    await bot.start(DISCORD_BOT_TOKEN)


async def create_listener_task(listener: Listen, queue: asyncio.Queue):
    await listener.start(queue)


async def main():
    queue = asyncio.Queue()
    billy_bot = BillyBot(queue)
    listener = Listen(openai_client, wolfram, youtube, giphy)

    if not discord.opus.is_loaded():
        discord.opus.load_opus("/opt/homebrew/lib/libopus.dylib")

    bot_task = asyncio.create_task(discord_bot_task(billy_bot))
    listener_task = asyncio.create_task(create_listener_task(listener, queue))
    queue_processor_task = asyncio.create_task(
        billy_bot.start_processor_task())

    await asyncio.gather(bot_task, listener_task, queue_processor_task)


if __name__ == "__main__":
    loop.run_until_complete(main())
