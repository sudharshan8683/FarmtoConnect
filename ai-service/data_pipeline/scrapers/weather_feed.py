import os
import requests
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

LOCATIONS = [
    {"district": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"district": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
    {"district": "Madurai", "lat": 9.9252, "lon": 78.1198},
    {"district": "Tiruppur", "lat": 11.1085, "lon": 77.3411},
]

def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata", "forecast_days": 1
    }
    r = requests.get(url, params=params, timeout=30,
                      headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()["daily"]

def save_weather():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            district VARCHAR(100),
            record_date DATE,
            temp_max NUMERIC(5,2),
            temp_min NUMERIC(5,2),
            rainfall_mm NUMERIC(6,2),
            UNIQUE(district, record_date)
        )
    """)
    conn.commit()

    for loc in LOCATIONS:
        d = fetch_weather(loc["lat"], loc["lon"])
        cur.execute("""
            INSERT INTO weather_data (district, record_date, temp_max, temp_min, rainfall_mm)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (district, record_date) DO UPDATE
            SET temp_max = EXCLUDED.temp_max, temp_min = EXCLUDED.temp_min, rainfall_mm = EXCLUDED.rainfall_mm
        """, (loc["district"], d["time"][0], d["temperature_2m_max"][0],
              d["temperature_2m_min"][0], d["precipitation_sum"][0]))
    conn.commit()
    cur.close()
    conn.close()
    print("Weather data updated for", len(LOCATIONS), "districts")

if __name__ == "__main__":
    save_weather()