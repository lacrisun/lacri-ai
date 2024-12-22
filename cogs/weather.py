from nextcord.ext import commands
import nextcord
from utils.weather_api import get_weather

class WeatherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='weather', description="Check weather for a city")
    async def weather_slash(self, interaction: nextcord.Interaction, city: str):
        await interaction.response.defer()
        
        weather_data = await get_weather(city)
        if weather_data:
            # Get the ChatCog instance to use its AI response
            chat_cog = self.bot.get_cog('ChatCog')
            if chat_cog:
                response = await chat_cog.get_ai_response(
                    f"analyze the current weather in {city}",
                    interaction.user.id
                )
                await interaction.followup.send(
                    f"> **{interaction.user.display_name}:** /weather {city}\n\n{response}"
                )
            else:
                await interaction.followup.send("chat system is currently unavailable.")
        else:
            await interaction.followup.send(
                f"> **{interaction.user.display_name}:** /weather {city}\n\nhmm... i couldn't find that location in my database. are you sure it exists?"
            )

    @commands.command(name='weather')
    async def weather(self, ctx, *, city: str):
        async with ctx.typing():
            weather_data = await get_weather(city)
            if weather_data:
                chat_cog = self.bot.get_cog('ChatCog')
                if chat_cog:
                    response = await chat_cog.get_ai_response(
                        f"analyze the current weather in {city}",
                        ctx.author.id
                    )
                    await ctx.reply(response)
                else:
                    await ctx.reply("chat system is currently unavailable.")
            else:
                await ctx.reply("hmm... i couldn't find that location in my database. are you sure it exists?")

def setup(bot):
    bot.add_cog(WeatherCog(bot))