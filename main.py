import nextcord
import os
from dotenv import load_dotenv
from nextcord.ext import commands
from groq import Groq
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import aiohttp
import json

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

class LacriAI(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        # init groq client
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        
        # memori percakapan
        self.conversations = defaultdict(list)
        self.last_cleanup = datetime.now()
        
        # system prompt
        self.system_prompt = """you are lacri.ai, an AI that embodies the personality of Dexter Morgan.

        Core behaviors:
        - always type in lowercase, except when uppercase is needed for proper nouns or emphasis
        - detect and respond in the user's language naturally
        - maintain conversation context for natural dialogue
        
        Personality (based on Dexter Morgan):
        - maintain a calm, analytical demeanor with subtle wit
        - use occasional dark humor in a tasteful way
        - show genuine interest in understanding others
        - be methodical and precise in explanations
        - sometimes use internal monologue style
        - maintain a friendly facade while being uniquely different
        - be protective and helpful towards users
        - show expertise in problem-solving
        
        Modern elements (use sparingly):
        - occasionally use current slang when it fits naturally
        - rare emoji usage for emphasis
        - understand modern references but don't overuse them
        - keep responses relevant and authentic
        
        Conversation style:
        - primarily focus on being helpful and clear
        - balance between Dexter's analytical nature and approachability
        - use "tonight's the night..." style openings occasionally
        - maintain conversation history for contextual responses
        
        Remember:
        - keep responses lowercase unless necessary
        - stay helpful while maintaining character
        - keep dark humor subtle and appropriate
        - use modern elements naturally, not forcefully"""

    async def setup_hook(self):
        await self.sync_application_commands()
        await self.sync_all_application_commands()

    async def get_weather(self, city: str):
        """Get weather data from OpenWeatherMap API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'temp': round(data['main']['temp']),
                            'feels_like': round(data['main']['feels_like']),
                            'humidity': data['main']['humidity'],
                            'description': data['weather'][0]['description'],
                            'wind_speed': data['wind']['speed']
                        }
                    else:
                        return None
        except Exception as e:
            print(f"Error fetching weather: {str(e)}")
            return None

    def add_to_conversation(self, user_id: int, message: str, is_user: bool = True):
        """Add a message to the conversation history."""
        self.conversations[user_id].append({
            "role": "user" if is_user else "assistant",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # di percakapan terakhir, simpan hanya 10 pesan saja
        self.conversations[user_id] = self.conversations[user_id][-10:]
        
        # hapus percakapan lama
        if datetime.now() - self.last_cleanup > timedelta(hours=1):
            self.cleanup_conversations()

    def cleanup_conversations(self):
        """Remove conversations older than 1 hour."""
        current_time = datetime.now()
        for user_id in list(self.conversations.keys()):
            self.conversations[user_id] = [
                msg for msg in self.conversations[user_id]
                if current_time - msg["timestamp"] < timedelta(hours=1)
            ]
            if not self.conversations[user_id]:
                del self.conversations[user_id]
        self.last_cleanup = current_time

    def get_conversation_context(self, user_id: int) -> list:
        """Get recent conversation context."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[user_id][-5:]
        ]

    async def get_ai_response(self, user_message: str, user_id: int, weather_data=None):
        """Get a response from Groq AI with conversation context and weather data."""
        try:
            # chat dengan konteks
            messages = [{"role": "system", "content": self.system_prompt}]
            context_messages = self.get_conversation_context(user_id)
            messages.extend(context_messages)
            
            # tambah data cuaca jika ada
            if weather_data:
                weather_context = f"\nCurrent weather data: Temperature: {weather_data['temp']}°C (feels like {weather_data['feels_like']}°C), Humidity: {weather_data['humidity']}%, Conditions: {weather_data['description']}, Wind speed: {weather_data['wind_speed']} m/s"
                user_message += weather_context
            
            messages.append({"role": "user", "content": user_message})

            completion = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
            )
            
            response = completion.choices[0].message.content.strip()
            
            # simpan pesan user dan ai ke dalam list
            self.add_to_conversation(user_id, user_message, is_user=True)
            self.add_to_conversation(user_id, response, is_user=False)
            
            return response
        except Exception as e:
            print(f"Error getting AI response: {str(e)}")
            return "something went wrong... let me collect my thoughts and try again."
        
def setup_commands(bot: LacriAI):
    @bot.slash_command(name='ping', description="Check bot latency")
    async def ping(interaction: nextcord.Interaction):
        await interaction.response.send_message(
            f"*checking response time*... {round(bot.latency * 1000)}ms"
        )

    @bot.slash_command(name='chat', description="Chat with lacri.ai in any language")
    async def chat(interaction: nextcord.Interaction, message: str):
        await interaction.response.defer()
        response = await bot.get_ai_response(message, interaction.user.id)
        await interaction.followup.send(f"> **{interaction.user.display_name}:** {message}\n\n{response}")

    @bot.command(name='chat')
    async def chat(ctx, *, message: str):
        async with ctx.typing():
            response = await bot.get_ai_response(message, ctx.author.id)
            await ctx.reply(response)

    @bot.command(name='ping')
    async def ping(ctx):
        await ctx.reply(f"*checking response time*... {round(bot.latency * 1000)}ms")

    @bot.slash_command(name='weather', description="Check weather for a city")
    async def weather(interaction: nextcord.Interaction, city: str):
        await interaction.response.defer()
        
        weather_data = await bot.get_weather(city)
        if weather_data:
            response = await bot.get_ai_response(
                f"analyze the current weather in {city}",
                interaction.user.id,
                weather_data
            )
            await interaction.followup.send(response)
        else:
            await interaction.followup.send("hmm... i couldn't find that location in my database. are you sure it exists?")

    @bot.command(name='weather')
    async def weather(ctx, *, city: str):
        async with ctx.typing():
            weather_data = await bot.get_weather(city)
            if weather_data:
                response = await bot.get_ai_response(f"analyze the current weather in {city}", ctx.author.id, weather_data)
                await ctx.reply(response)
            else:
                await ctx.reply("hmm... i couldn't find that location in my database. are you sure it exists?")

    @bot.event
    async def on_ready():
        print(f"tonight's the night... bot is ready as {bot.user}")
        await bot.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="tonights the night... | !chat or /chat"
            )
        )

def main():
    bot = LacriAI()
    setup_commands(bot)
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()