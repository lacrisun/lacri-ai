import aiohttp
from config import WEATHER_API_KEY

async def get_weather(city: str):
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