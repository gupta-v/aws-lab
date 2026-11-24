from datetime import datetime, timezone

import httpx
from ddgs import DDGS
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq


@tool
def get_time() -> str:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc).isoformat()


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city name, e.g. 'Pune'."""
    # Open-Meteo: free, no API key. Two calls: city -> lat/lon, then lat/lon -> weather.
    geo = httpx.get("https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1}, timeout=10).json()
    if not geo.get("results"):
        return f"error: city '{city}' not found"
    place = geo["results"][0]
    cur = httpx.get("https://api.open-meteo.com/v1/forecast",
                    params={"latitude": place["latitude"], "longitude": place["longitude"],
                            "current": "temperature_2m,wind_speed_10m,weather_code"},
                    timeout=10).json()["current"]
    return (f"{place['name']}, {place.get('country', '')}: {cur['temperature_2m']}°C, "
            f"wind {cur['wind_speed_10m']} km/h, weather code {cur['weather_code']}")


@tool
def web_search(query: str) -> str:
    """Search the web and return the top results (title, link, snippet)."""
    try:
        hits = DDGS().text(query, max_results=3)
    except Exception as e:  # ddgs raises on no results / rate limits; let the model see it instead of crashing
        return f"error: search failed ({e})"
    return "\n".join(f"{h['title']} - {h['href']}\n{h['body']}" for h in hits) or "no results"


# INIT: built once per execution environment
agent = create_agent(
    ChatGroq(model="openai/gpt-oss-120b"),
    tools=[get_time, get_weather, web_search],
    system_prompt="You are Info Buddy. Be brief. Use tools for time, weather and facts you don't know.",
)


def chat(message: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": message}]})
    return result["messages"][-1].content
