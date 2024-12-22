from nextcord.ext import commands
import nextcord
from groq import Groq
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from config import GROQ_API_KEY

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.conversations = defaultdict(list)
        self.last_cleanup = datetime.now()
        self.bot_messages = {}
        
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

    def cog_unload(self):
        self.conversations.clear()
        self.bot_messages.clear()

    def add_to_conversation(self, user_id: int, message: str, is_user: bool = True):
        self.conversations[user_id].append({
            "role": "user" if is_user else "assistant",
            "content": message,
            "timestamp": datetime.now()
        })
        
        self.conversations[user_id] = self.conversations[user_id][-10:]
        
        if datetime.now() - self.last_cleanup > timedelta(hours=1):
            self.cleanup_conversations()

    def cleanup_conversations(self):
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
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[user_id][-5:]
        ]

    async def get_ai_response(self, user_message: str, user_id: int):
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            context_messages = self.get_conversation_context(user_id)
            messages.extend(context_messages)
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
            
            self.add_to_conversation(user_id, user_message, is_user=True)
            self.add_to_conversation(user_id, response, is_user=False)
            
            return response
        except Exception as e:
            print(f"Error getting AI response: {str(e)}")
            return "something went wrong... let me collect my thoughts and try again."

    @nextcord.slash_command(name='chat', description="Chat with lacri.ai in any language")
    async def chat_slash(self, interaction: nextcord.Interaction, message: str):
        await interaction.response.defer()
        response = await self.get_ai_response(message, interaction.user.id)
        await interaction.followup.send(
            f"> **{interaction.user.display_name}:** {message}\n\n{response}"
        )

    @commands.command(name='chat')
    async def chat(self, ctx, *, message: str):
        async with ctx.typing():
            response = await self.get_ai_response(message, ctx.author.id)
            await ctx.reply(response)

def setup(bot):
    bot.add_cog(ChatCog(bot))