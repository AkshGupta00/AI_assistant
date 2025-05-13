import geocoder
import requests
import spacy


nlp = spacy.load("en_core_web_sm")



weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}



def get_current_weather(latitude, longitude):
    """Fetch current weather data."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&timezone=Asia/Kolkata"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if "current_weather" in data:
            current_weather = data['current_weather']
            weather = f"""Current Weather:\n
            Temperature: {current_weather['temperature']}°C\n
            Wind Speed: {current_weather['windspeed']} km/h\n
            Weather: {weather_codes[current_weather['weathercode']]}\n"""
            return True, weather
        else:
            return False ,"Failed to retrieve valid weather data."
    except requests.exceptions.RequestException as e:
        return False,f"Error occurred: {e}"

def get_daily_forecast(latitude, longitude,i):
    """Fetch daily weather forecast."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset,weather_code&timezone=Asia/Kolkata"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if "daily" in data:
            daily = data['daily']
            
            weather = f"""Date: {daily['time'][i]}: Max Temp: {daily['temperature_2m_max'][i]}°C, Min Temp: {daily['temperature_2m_min'][i]}°C\n
            "Precipitation: {daily['precipitation_sum'][i]} mm\n
            Weather: {weather_codes[daily['weather_code'][i]]}\n
            Sunrise: {daily['sunrise'][i]}, Sunset: {daily['sunset'][i]}\n"""
            return True, weather
        else:
            return False,"Failed to retrieve daily forecast data."
    except requests.exceptions.RequestException as e:
        False, f"Error occurred: {e}"

def get_hourly_forecast(latitude, longitude):
    """Fetch hourly weather forecast."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if "hourly" in data:
            hourly = data['hourly']
            print("Hourly Forecast:")
            for i in range(len(hourly['temperature_2m'])):
                print(f"Hour {i + 1}: Temp: {hourly['temperature_2m'][i]}°C, Humidity: {hourly['relative_humidity_2m'][i]}%, Wind Speed: {hourly['wind_speed_10m'][i]} km/h")
                print("-" * 40)
        else:
            print("Failed to retrieve hourly forecast data.")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")


def intent_detection(command):
    """Detects intent based on the command using spaCy and multi-word sequences."""
    command = command.lower()
    doc = nlp(command)
    
    # Intent mapping with multi-word phrases
    intents = {
        "current": ["today", "now", "current", "right now"],
        "tomorrow": ["tomorrow"],
        "datomorrow": ["dayaftertomorrow", " intwodays"],
    }
    no_space_cmd = command.replace(" ","")

    for phrases in intents["datomorrow"]:
        if phrases in no_space_cmd:
            return "datomorrow"
    
    for intent, phrases in intents.items():
        for phrase in phrases:
            if phrase in command:
                return intent
    
    # Default to "current" if no match is found
    return "current"


def process_weather_cmd(command):
    """Process a weather command from the user."""
    intent = intent_detection(command)
    g = geocoder.ip('me')
    cords = g.latlng  # [latitude, longitude]
    
    if not cords:
        return "Could not determine your location. you can check it by going out.","Could not determine your location.you can check it by going out."
    
    latitude, longitude = cords[0], cords[1]

    if intent == "current":
        flag, weather = get_current_weather(latitude, longitude)
        if flag:
            return weather,"the weather today is"
        else :
            return "go look outside and feel it yourself","go look outside and feel it yourself"
    elif intent == "tomorrow":
        flag, message = get_daily_forecast(latitude, longitude, 1)
        if flag:
            return message,"the weather tomorrow will be"
        return "something went wrong while trying to ask god for weather","something went wrong while trying to ask god for weather"
    elif intent == "datomorrow":
        flag, message = get_daily_forecast(latitude, longitude, 2)
        if flag:
            return message,"the weather day after tomorrow will be"
        return "something went wrong while trying to ask god for weather","something went wrong while trying to ask god for weather"
    else:
        return "I didn't understand that. Can you try again?"
    