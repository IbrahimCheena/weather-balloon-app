from flask import Flask, jsonify
import requests
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend to access backend

# Windborne API URL
BASE_URL = "https://a.windbornesystems.com/treasure/"

# Weather API (replace with your API key)
WEATHER_API_KEY = "K57A2P9YSHBVDWRKMCMF3Y6N2"
WEATHER_URL = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/palo%20alto?unitGroup=us&key={WEATHER_API_KEY}&contentType=json"


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


def fetch_balloon_data():
    """
    Fetch the latest balloon data and handle errors.
    """
    try:
        response = requests.get(BASE_URL + "00.json", timeout=5)
        response.raise_for_status()
        data = response.json()

        # Sanitize the data to replace NaN values
        sanitized_data = sanitize_data(data)

        # Transform the balloon data into a list of objects
        transformed_data = []
        for index, balloon in enumerate(sanitized_data):
            if isinstance(balloon, list) and len(balloon) == 3:  # Ensure valid structure
                transformed_data.append({
                    "id": index + 1,  # Generate an ID
                    "lat": balloon[0] if balloon[0] is not None else "N/A",
                    "lon": balloon[1] if balloon[1] is not None else "N/A",
                    "alt": balloon[2] if balloon[2] is not None else "N/A"
                })

        return transformed_data  # Return the transformed data
    except (requests.RequestException, ValueError):
        return []  # Return an empty list if there's an error or corrupted data


def fetch_historical_balloon_data(hours_ago):
    """
    Fetch balloon data from `hours_ago` hours ago.
    """
    try:
        url = BASE_URL + f"{hours_ago:02d}.json"  # Format URL (e.g., 01.json, 02.json)
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Sanitize the data to replace NaN values
        sanitized_data = sanitize_data(data)

        # Transform the balloon data into a list of objects
        transformed_data = []
        for index, balloon in enumerate(sanitized_data):
            if isinstance(balloon, list) and len(balloon) == 3:  # Ensure valid structure
                transformed_data.append({
                    "id": index + 1,  # Generate an ID
                    "lat": balloon[0] if balloon[0] is not None else "N/A",
                    "lon": balloon[1] if balloon[1] is not None else "N/A",
                    "alt": balloon[2] if balloon[2] is not None else "N/A",
                    "hours_ago": hours_ago  # Add a timestamp for historical data
                })

        return transformed_data
    except (requests.RequestException, ValueError):
        return []  # Return an empty list if there's an error or corrupted data


def fetch_weather_data():
    """
    Fetch weather data for Palo Alto.
    """
    try:
        response = requests.get(WEATHER_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return sanitize_data(data)  # Sanitize data before returning
    except (requests.RequestException, ValueError):
        return None  # Handles API errors


@app.route('/data', methods=['GET'])
def get_data():
    """
    Combine balloon and weather data, including historical balloon data.
    """
    balloon_data = fetch_balloon_data()
    weather_data = fetch_weather_data()

    # Fetch historical balloon data (e.g., 1 hour ago, 3 hours ago)
    historical_data = []
    for hours_ago in [1, 3]:  # Add more hours as needed
        historical_data.extend(fetch_historical_balloon_data(hours_ago))

    if not balloon_data or not weather_data:
        return jsonify({"error": "Failed to fetch data from APIs"}), 500

    combined_data = {
        "weather": weather_data,
        "balloons": balloon_data,
        "historical_balloons": historical_data
    }

    # Log the combined data for debugging
    print("Combined Data:", combined_data)

    return jsonify(combined_data)


if __name__ == '__main__':
    app.run(debug=True)