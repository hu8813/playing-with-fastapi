"""
weather-api
An unofficial API interface for retrieving weather information from OpenWeatherMap.

This project is provided as is, without any warranty or support,
and is not affiliated with any weather service in any way.

This project is licensed under the GNU General Public License v3.0.
For more information, please visit https://www.gnu.org/licenses/gpl-3.0.html.
"""

import asyncio
import datetime
import os
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

app = FastAPI()

# Cache for storing weather data
weather_cache = {}

async def refresh_weather_data(city: str):
    """
    Refreshes the weather data every 24 hours for a specific city.
    """
    global weather_cache  # needed to modify the global weather_cache object

    while True:
        await asyncio.sleep(60*60*24)  # refresh every 24 hours
        weather_cache[city] = fetch_weather(city)

def fetch_weather(city: str):
    """
    Fetches weather data for a specific city from OpenWeatherMap.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"  # to get temperature in Celsius
    }
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        weather_info = {
            "temperature": f"{data['main']['temp']}°C",
            "humidity": f"{data['main']['humidity']}%",
            "condition": data['weather'][0]['description']
        }
        return weather_info
    else:
        # Log the error detail for debugging
        print(f"Error fetching weather data for {city}: {response.status_code} - {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.json())

@app.on_event("startup")
async def startup_event():
    """Creates sub-processes to run in the background when the server starts."""
    cities = ["London", "New York", "Tokyo"]  # Add initial cities to fetch weather data
    for city in cities:
        try:
            weather_cache[city] = fetch_weather(city)
            asyncio.create_task(refresh_weather_data(city))
        except HTTPException as e:
            print(f"Failed to fetch initial data for {city}: {e.detail}")

@app.get(path="/", description="Get the root endpoint.")
async def get_root():
    """Endpoint to get the root tree of the API."""
    return {"message": "Welcome to the Weather API. Use endpoints /weather/{city} to get weather information."}

@app.get(path="/weather/{city}", description="Get weather information for a specific city.")
async def get_weather(city: str):
    """Endpoint to get weather information for a specific city."""
    try:
        if city not in weather_cache:
            weather_cache[city] = fetch_weather(city)
        return weather_cache[city]
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content=e.detail)

@app.get(path="/today/{city}", description="Get today's weather information for a specific city.")
async def get_today_weather(city: str):
    """Endpoint to get today's weather information for a specific city."""
    try:
        return fetch_weather(city)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content=e.detail)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, loop="asyncio")
