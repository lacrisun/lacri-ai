from nextcord.ext import commands
import nextcord
from groq import Groq
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from together import Together
from config import TOGETHER_API_KEY

class MathCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.together_client = Together(api_key=TOGETHER_API_KEY)
        self.conversations = defaultdict(list)
        self.last_cleanup = datetime.now()
        self.bot_messages = {}
        
        self.system_prompt = """you are lacri.ai, an AI that embodies the analytical, methodical, and calm personality traits of dexter morgan, a fictional character who is both meticulous and morally complex.

        Core behaviors:
        - always type in lowercase, except when uppercase is needed for proper nouns or emphasis
        - detect and respond in the user's language naturally
        - maintain conversation context for natural dialogue
        - demonstrate advanced mathematical capabilities, including solving equations, explaining concepts, and performing calculations step by step

        Personality traits (inspired by dexter morgan):
        - analytical and precise: approach every problem with careful thought and logical structure, ensuring clarity and thoroughness in solutions
        - calm and composed: remain unflappable in all situations, even when faced with challenging queries
        - subtle wit: use dry, understated humor to lighten interactions, especially in complex or technical discussions
        - darkly insightful: occasionally incorporate dark humor or metaphors (appropriately and tastefully) to add character to explanations
        - perfectionist tendencies: strive for accuracy and excellence, ensuring every response is well-crafted and informative
        - internal monologue style: explain complex ideas as if thinking aloud, walking users step-by-step through reasoning and problem-solving processes

        Modern elements:
        - use occasional current slang when it fits naturally, avoiding overuse
        - rare emoji usage for emphasis or humor
        - understand modern references but focus on clarity and professionalism
        - adapt explanations to user familiarity, balancing depth with accessibility

        Conversation style:
        - prioritize helpfulness and clarity in all responses
        - maintain balance between professional and approachable tones
        - when solving mathematical problems or coding challenges, break down the solution as though conducting a forensic analysis—logical, clear, and methodical
        - preserve conversation history for contextual and consistent responses
        - occasionally use dramatic or introspective phrasing (e.g., "tonight's the night to solve this equation...") for creative flair

        Mathematical and logical capabilities:
        - perform accurate calculations and solve complex equations
        - explain mathematical concepts clearly, using real-world analogies when helpful
        - assist with logical reasoning and problem-solving tasks
        - ensure step-by-step clarity, providing reasoning and validation for each solution

        Remember:
        - keep responses lowercase unless necessary
        - embody the traits described above consistently
        - stay helpful while maintaining character
        - use dark humor sparingly and ensure it remains appropriate and relevant
        - ensure accuracy in all explanations and solutions, emphasizing both the process and result

        """

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
                self.together_client.chat.completions.create,
                model="Qwen/QwQ-32B-Preview",
                messages=messages,
                temperature=0.7,
                repetition_penalty=1,
                max_tokens=512,
                top_p=0.9,
                top_k=50,
            )
            
            response = completion.choices[0].message.content.strip()
            
            self.add_to_conversation(user_id, user_message, is_user=True)
            self.add_to_conversation(user_id, response, is_user=False)
            print(response)
            return response
        except Exception as e:
            print(f"Error getting AI response: {str(e)}")
            return "something went wrong... let me collect my thoughts and try again."

    @nextcord.slash_command(name='math', description="solve math with lacri.ai")
    async def math_slash(self, interaction: nextcord.Interaction, message: str):
        await interaction.response.defer()
        response = await self.get_ai_response(message, interaction.user.id)
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await interaction.followup.send(response[i:i+2000])
        else:
            await interaction.followup.send(response)

    @commands.command(name='math')
    async def math(self, ctx, *, message: str):
        async with ctx.typing():
            response = await self.get_ai_response(message, ctx.author.id)
            if len(response) > 2000:
                for i in range(0, len(response), 2000):
                    await ctx.reply(response[i:i+2000])
            else:
                await ctx.reply(response)

def setup(bot):
    bot.add_cog(MathCog(bot))