import os
import requests
from flask import Blueprint, jsonify
from dotenv import load_dotenv

load_dotenv()

weather_bp = Blueprint('weather', __name__, url_prefix='/api/weather')

# Get your API key
API_KEY = os.environ.get('OPENWEATHER_API_KEY')
CITY = os.environ.get('CITY')
STATE = os.environ.get('STATE')
# We'll use College Station, TX. You can change this.
CITY = "College Station"
STATE = "TX"
COUNTRY = "US"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


@weather_bp.route('/', methods=['GET'])
def get_weather():
    """
    Fetches the current weather from the OpenWeatherMap API.
    This is a secure endpoint; the API key never leaves the server.
    """
    if not API_KEY:
        return jsonify({"error": "Weather API key not configured"}), 500

    # Construct the full API URL
    query_params = f"?q={CITY},{STATE},{COUNTRY}&appid={API_KEY}&units=imperial"
    full_url = BASE_URL + query_params

    try:
        # Call the external API
        response = requests.get(full_url)
        response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)

        data = response.json()

        # Simplify the data to send to the frontend
        # This is good practice! Only send what you need.
        weather_data = {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "city": data["name"]
        }

        return jsonify(weather_data)

    except requests.exceptions.RequestException as e:
        # Handle errors (e.g., API key wrong, network down)
        print(f"Error fetching weather: {e}")
        return jsonify({"error": "Could not fetch weather data"}), 503
    except KeyError:
        # Handle unexpected JSON structure
        return jsonify({"error": "Unexpected data format from weather API"}), 500
