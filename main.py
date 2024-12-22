import nextcord
from nextcord.ext import commands
import os
from config import DISCORD_TOKEN

class LacriAI(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded {filename[:-3]} cog')
                except Exception as e:
                    print(f'Failed to load {filename[:-3]} cog: {str(e)}')

    async def on_ready(self):
        print(f"tonight's the night... bot is ready as {self.user}")
        await self.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="carefully... | !chat or /chat"
            )
        )

def main():
    bot = LacriAI()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()