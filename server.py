from flask import Flask, jsonify
from flask_cors import CORS
import requests
import math

app = Flask(__name__)
CORS(app)

WEATHER_API_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Palo%20Alto"
WEATHER_API_KEY = "K57A2P9YSHBVDWRKMCMF3Y6N2"
BALLOON_API_URL = "https://a.windbornesystems.com/treasure/00.json"


def sanitize_data(data):
    """
    Recursively replace NaN values with null in a dictionary or list.
    """
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) if not (isinstance(v, float) and math.isnan(v)) else None for v in data]
    elif isinstance(data, float) and math.isnan(data):
        return None
    else:
        return data


@app.route('/')
def home():
    return "Flask server is running! Use /data to get API response."


@app.route('/favicon.ico')
def favicon():
    return '', 204  # Ignore favicon requests


@app.route('/data', methods=['GET'])
def get_data():
    try:
        # Fetch weather data from the weather API
        weather_response = requests.get(f"{WEATHER_API_URL}?unitGroup=us&key={WEATHER_API_KEY}&contentType=json")
        
        # Check if the weather API returned a successful response
        if weather_response.status_code != 200:
            return jsonify({"error": "Weather data API error", "status_code": weather_response.status_code}), 500
        
        # Try to parse the weather data into JSON
        weather_data = weather_response.json()

        # Fetch balloon data from the balloon API
        balloon_response = requests.get(BALLOON_API_URL)
        
        # Check if the balloon API returned a successful response
        if balloon_response.status_code != 200:
            return jsonify({"error": "Balloon data API error", "status_code": balloon_response.status_code}), 500
        
        # Try to parse the balloon data into JSON
        balloon_data = balloon_response.json()
        
        # Debug: Log balloon data to see what is returned from the balloon API
        print("Raw Balloon Data:", balloon_data)

        # Sanitize the balloon data to replace NaN values with null
        sanitized_balloon_data = sanitize_data(balloon_data)

        # If balloon data is not a list, return an empty list (to avoid errors)
        if not isinstance(sanitized_balloon_data, list):
            sanitized_balloon_data = []

        # Combine the weather data and balloon data
        combined_data = {
            "weather": weather_data,
            "balloons": sanitized_balloon_data
        }

        # Debug: Log combined data for debugging
        print("Combined Data:", combined_data)

        return jsonify(combined_data)

    except requests.exceptions.RequestException as req_err:
        # Catch any issues with the requests (network, timeout, etc.)
        return jsonify({"error": f"Request failed: {str(req_err)}"}), 500

    except ValueError as json_err:
        # Catch issues with JSON parsing
        return jsonify({"error": f"JSON parsing error: {str(json_err)}"}), 500

    except Exception as e:
        # Catch any other exceptions
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)