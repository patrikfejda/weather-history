import requests
import psycopg2
import datetime
import sys

# Get PostgreSQL credentials from command-line arguments
if len(sys.argv) != 3:
    print("Usage: python main.py <PGUSER> <PGPASSWORD>")
    sys.exit(1)

PGUSER = sys.argv[1]
PGPASSWORD = sys.argv[2]

def fetch_weather():
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    params = {
        "lat": "48.1486",  # Bratislava latitude
        "lon": "17.1077"   # Bratislava longitude
    }
    headers = {
        "User-Agent": "YourAppName/1.0 (your.email@example.com)"  # Replace with your info
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Get the first timeseries entry as current weather
    current = data["properties"]["timeseries"][0]
    obs_time = current["time"]
    details = current["data"]["instant"]["details"]
    temperature = details.get("air_temperature")
    wind_speed_mps = details.get("wind_speed")
    wind_kmh = wind_speed_mps * 3.6 if wind_speed_mps is not None else None

    # Try to get rain (precipitation) info if available in the next_1_hours forecast
    rain_mm = None
    if "next_1_hours" in current["data"]:
        rain_mm = current["data"]["next_1_hours"]["details"].get("precipitation_amount")

    return {
        "observation_time": obs_time,
        "temperature_celsius": temperature,
        "wind_kmh": wind_kmh,
        "rain_mm": rain_mm
    }

def save_to_db(weather_data):
    conn = psycopg2.connect(f"postgresql://{PGUSER}:{PGPASSWORD}@ep-withered-lab-a2d3en58-pooler.eu-central-1.aws.neon.tech/weather")
    cur = conn.cursor()
    insert_query = """
    INSERT INTO weather_history (observation_time, temperature_celsius, wind_kmh, rain_mm)
    VALUES (%s, %s, %s, %s);
    """
    # Convert observation time to datetime object
    obs_time_dt = datetime.datetime.fromisoformat(weather_data["observation_time"].replace("Z", "+00:00"))
    cur.execute(insert_query, (obs_time_dt, weather_data["temperature_celsius"],
                               weather_data["wind_kmh"], weather_data["rain_mm"]))
    conn.commit()
    cur.close()
    conn.close()

def main():
    weather = fetch_weather()
    print("Fetched weather data:", weather)
    save_to_db(weather)
    print("Weather data saved to database.")

if __name__ == "__main__":
    main()
