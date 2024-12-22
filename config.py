import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SAMBANOVA_API_KEY = os.getenv('SAMBANOVA_API_KEY')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')

# Bot settings
COMMAND_PREFIX = "!"