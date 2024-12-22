from nextcord.ext import commands
import nextcord

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.conversations.clear()
        self.bot_messages.clear()

    @nextcord.slash_command(name='ping', description="Check bot latency")
    async def ping_slash(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            f"> **Ping request**\n*checking response time*... {round(self.bot.latency * 1000)}ms"
        )

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.reply(f"*checking response time*... {round(self.bot.latency * 1000)}ms")

def setup(bot):
    bot.add_cog(UtilityCog(bot))