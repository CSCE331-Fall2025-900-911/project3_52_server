import os
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

load_dotenv()

translate_bp = Blueprint('translate', __name__, url_prefix='/api/translate')

# Initialize the Google Translate client
# The library automatically finds the API key from the environment
# if you set it as GOOGLE_APPLICATION_CREDENTIALS, but for
# a simple key, we'll initialize it manually.
# NOTE: google-cloud-translate-v2 library is a bit particular.
# For API Key auth, it's often easier to just use 'requests'
# as the client library is designed for service accounts.
#
# Let's pivot to a 'requests' based approach like OpenWeather.
# It's simpler and doesn't require complex auth setup.

import requests

API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
BASE_URL = "https://translation.googleapis.com/language/translate/v2"


@translate_bp.route('/', methods=['POST'], strict_slashes=False)
def handle_translate():
    """
    Fetches a translation from the Google Translate API.
    The frontend must send a JSON body with:
    {
        "text": "The text to translate",
        "target_language": "es" (e.g., "es" for Spanish)
    }
    """
    if not API_KEY:
        return jsonify({"error": "Translation API key not configured"}), 500

    data = request.get_json()

    text_to_translate = data.get('text')
    target_language = data.get('target_language')

    if not text_to_translate or not target_language:
        return jsonify({"error": "Missing 'text' or 'target_language' in request body"}), 400

    # Construct the query parameters
    params = {
        'q': text_to_translate,
        'target': target_language,
        'key': API_KEY,
        'format': 'text'
    }

    try:
        # Call the external API
        response = requests.post(BASE_URL, params=params)
        response.raise_for_status()  # Raises an error for bad responses

        json_response = response.json()

        # Extract the translated text from the complex response
        translated_text = json_response['data']['translations'][0]['translatedText']

        return jsonify({
            "original_text": text_to_translate,
            "translated_text": translated_text,
            "target_language": target_language
        })

    except requests.exceptions.RequestException as e:
        print(f"Error calling Translate API: {e}")
        return jsonify({"error": "Could not fetch translation"}), 503
    except KeyError:
        print(f"Unexpected JSON response from Translate API: {json_response}")
        return jsonify({"error": "Unexpected data format from translate API"}), 500
