# Lacri.AI Discord Bot

A Discord bot powered by Groq AI that embodies the personality of Dexter Morgan while providing helpful assistance to users.

## Features

- Chat with AI using Groq's llama-3.3-70b-versatile model
- Weather information integration
- Multi-language support
- Conversation memory
- Both slash commands and regular commands

## Commands

- `/chat [message]` or `!chat [message]` - Chat with the AI
- `/weather [city]` or `!weather [city]` - Get weather information for a city
- `/ping` or `!ping` - Check bot latency
- `/math` or `!math` - Mathematical capablities (not recommended to use)
- `/program` or `!program` - Use lacri.ai to help with your coding problems with Qwen-2.5 Coder

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/your-bot-repo.git
cd your-bot-repo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your tokens:
```
DISCORD_TOKEN=your_discord_token_here
GROQ_API_KEY=your_groq_api_key_here
WEATHER_API_KEY=your_weather_api_key_here
```

4. Run the bot:
```bash
python main.py
```

## Deployment

### Local Development
1. Set up your virtual environment
2. Install dependencies
3. Create `.env` file
4. Run the bot

### Hosting Platforms
- **PylexNodes**
- **Heroku**
- **pella**

## Environment Variables

Create a `.env` file with the following:
- `DISCORD_TOKEN`: Your Discord bot token
- `GROQ_API_KEY`: Your Groq API key
- `WEATHER_API_KEY`: Your OpenWeatherMap API key

## Contributing

Feel free to submit issues and pull requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details
