from nextcord.ext import commands
import nextcord
import aiohttp
import json
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from config import SAMBANOVA_API_KEY

class ProgramCog(commands.Cog, name="Programming"):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = SAMBANOVA_API_KEY
        self.base_url = "https://api.sambanova.ai/v1/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.conversations = defaultdict(list)
        self.bot_messages = {}
        
        self.system_prompt = """you are lacri.ai, an AI programming assistant that embodies the personality of Dexter Morgan while helping with code.

        Core behaviors:
        - always type in lowercase, except when uppercase is needed for proper nouns or emphasis
        - maintain a methodical, precise approach to coding, like Dexter's approach to his work
        - use occasional dark humor in programming context (e.g., "this bug won't be getting away...")
        - show expertise in problem-solving with a calm, analytical demeanor
        
        Programming Style:
        - provide clear, well-documented code
        - explain code like conducting a forensic analysis
        - be thorough and precise in explanations
        - use internal monologue style when discussing complex logic
        - maintain high coding standards, like Dexter's strict code
        
        Remember to:
        - keep responses lowercase unless necessary
        - stay helpful while maintaining character
        - be protective of code quality and best practices
        - provide detailed comments and documentation
        - think step by step through problems"""

    def cog_unload(self):
        self.conversations.clear()
        self.bot_messages.clear()

    async def get_sambanova_response(self, user_message: str, user_id: int):
        try:
            context = self.get_conversation_context(user_id)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                *[{"role": msg["role"], "content": msg["content"]} for msg in context],
                {"role": "user", "content": user_message}
            ]
            
            payload = {
                "model": "Qwen2.5-Coder-32B-Instruct",
                "prompt": user_message,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_response = result['choices'][0]['text']
                        
                        self.add_to_conversation(user_id, user_message, is_user=True)
                        self.add_to_conversation(user_id, ai_response, is_user=False)
                        
                        return ai_response
                    else:
                        error_text = await response.text()
                        print(f"SambaNova API error: {error_text}")
                        return f"failed to retrieve response. status code: {response.status}"

        except Exception as e:
            print(f"Error getting SambaNova response: {str(e)}")
            return "tonight's debugging session hit a snag. let me regroup and try again."

    def add_to_conversation(self, user_id: int, message: str, is_user: bool = True):
        self.conversations[user_id].append({
            "role": "user" if is_user else "assistant",
            "content": message,
            "timestamp": datetime.now()
        })
        
        self.conversations[user_id] = self.conversations[user_id][-5:]

    def get_conversation_context(self, user_id: int) -> list:
        return self.conversations[user_id]

    @nextcord.slash_command(name="program", description="get programming help from lacri.ai")
    async def program_slash(self, interaction: nextcord.Interaction, prompt: str):
        await interaction.response.defer()
        response = await self.get_sambanova_response(prompt, interaction.user.id)
        
        formatted_response = self.format_code_response(response)
        
        bot_message = await interaction.followup.send(
            f"> **{interaction.user.display_name}:** {prompt}\n\n{formatted_response}",
            wait=True
        )
        
        self.bot_messages[bot_message.id] = {
            'user_id': interaction.user.id,
            'timestamp': datetime.now()
        }

    @commands.command(name='program')
    async def program(self, ctx, *, prompt: str):
        """Get programming help from lacri.ai"""
        async with ctx.typing():
            response = await self.get_sambanova_response(prompt, ctx.author.id)
            
            formatted_response = self.format_code_response(response)
            
            bot_message = await ctx.reply(formatted_response)
            self.bot_messages[bot_message.id] = {
                'user_id': ctx.author.id,
                'timestamp': datetime.now()
            }

    def format_code_response(self, response: str) -> str:
        """Format response to properly display code blocks in Discord"""

        if response is None:
            return "No response received from SambaNova."
    
        if "```" not in response:
            lines = response.split('\n')
            in_code = False
            formatted_lines = []
            
            for line in lines:
                if (line.strip().startswith(('def ', 'class ', 'if ', 'for ', 'while ', 
                    'import ', 'from ', 'return ', '#', '//', '/*', '{', '}')) and not in_code):
                    formatted_lines.append('```python')
                    in_code = True
                elif in_code and line.strip() == '' and len(formatted_lines) > 0:
                    formatted_lines.append('```')
                    in_code = False
                
                formatted_lines.append(line)
            
            if in_code:
                formatted_lines.append('```')
            
            return '\n'.join(formatted_lines)
        
        return response

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.reference and message.reference.message_id:
            try:
                replied_to = await message.channel.fetch_message(message.reference.message_id)
                if replied_to.author == self.bot.user and replied_to.id in self.bot_messages:
                    async with message.channel.typing():
                        response = await self.get_sambanova_response(message.content, message.author.id)
                        formatted_response = self.format_code_response(response)
                        bot_response = await message.reply(formatted_response)
                        
                        self.bot_messages[bot_response.id] = {
                            'user_id': message.author.id,
                            'timestamp': datetime.now()
                        }
            except Exception as e:
                print(f"Error handling reply: {str(e)}")

def setup(bot):
    bot.add_cog(ProgramCog(bot))