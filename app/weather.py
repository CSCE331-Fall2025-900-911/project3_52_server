import os
import requests
from flask import Blueprint, jsonify, request  # <-- Import 'request'
from dotenv import load_dotenv

load_dotenv()

weather_bp = Blueprint('weather', __name__, url_prefix='/api/weather')

# Get your API key
API_KEY = os.environ.get('OPENWEATHER_API_KEY')

# Remove the old hard-coded location
# CITY = "College Station"
# STATE = "TX"
# COUNTRY = "US"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Default coordinates for College Station
CSTAT_LAT = "32.05"
CSTAT_LON = "118.80"


@weather_bp.route('/', methods=['GET'], strict_slashes=False)
def get_weather():
    """
    Fetches the current weather from the OpenWeatherMap API.
    It accepts 'lat' and 'lon' query parameters.
    If they are missing, it defaults to College Station.
    """
    if not API_KEY:
        return jsonify({"error": "Weather API key not configured"}), 500

    # --- THIS IS THE NEW LOGIC ---
    # Get lat/lon from the request URL (e.g., /api/weather?lat=...&lon=...)
    # If they aren't provided, use the CStat defaults
    lat = request.args.get('lat', default=CSTAT_LAT)
    lon = request.args.get('lon', default=CSTAT_LON)
    # --- END NEW LOGIC ---

    # Construct the full API URL using lat/lon
    query_params = f"?lat={lat}&lon={lon}&appid={API_KEY}&units=imperial"
    full_url = BASE_URL + query_params

    try:
        # Call the external API
        response = requests.get(full_url)
        response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)

        data = response.json()

        # Simplify the data to send to the frontend
        weather_data = {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "city": data["name"]
        }

        return weather_data;

    except requests.exceptions.RequestException as e:
        # Handle errors (e.g., API key wrong, network down)
        print(f"Error fetching weather: {e}")
        return jsonify({"error": "Could not fetch weather data"}), 503
    except KeyError:
        # Handle unexpected JSON structure
        return jsonify({"error": "Unexpected data format from weather API"}), 500

