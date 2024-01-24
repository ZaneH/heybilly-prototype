import asyncio
import discord


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

            await self.send_nsfw(item)

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        self.ready_event.set()

    async def send_nsfw(self, message):
        print("Sending message: ", message)
        channel = self.get_channel(976623220759339058)
        await channel.send(message)
