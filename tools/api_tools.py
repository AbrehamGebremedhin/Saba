
# Only keep the correct, DRY, string-compatible APITools implementation
import httpx
from config.config import Settings
from langchain_core.tools import tool

class APITools:
    def __init__(self):
        self.settings = Settings()

    async def _fetch(self, url: str, headers: dict = None) -> dict:
        """Generic async GET request helper."""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return {}
            except Exception:
                return {}

    async def _get_location_raw(self, ipAddress: str = "") -> str:
        url = f'https://ipinfo.io/json?token={self.settings.IPINFO_KEY}'
        data = await self._fetch(url)
        return data.get('city', '') if isinstance(data, dict) else ''

    async def _get_weather_raw(self, city: str) -> dict:
        url = (
            f"https://api.tomorrow.io/v4/weather/realtime"
            f"?location={city}&apikey={self.settings.WEATHER_API_KEY}"
        )
        return await self._fetch(url)

    async def _get_movie_info_raw(self, title: str) -> dict:
        url = f"http://www.omdbapi.com/?t={title}&apikey={self.settings.OMDB_API_KEY}"
        return await self._fetch(url)

    async def _get_anime_info_raw(self, title: str) -> dict:
        api_url = (
            f"https://api.myanimelist.net/v2/anime?q={title}"
            "&limit=1&fields=synopsis,genres,media_type,nsfw,num_episodes,"
            "status,source,title,rating,related_anime"
        )
        headers = {"X-MAL-CLIENT-ID": self.settings.MAL_API_CLIENT_ID}
        return await self._fetch(api_url, headers=headers)

    # -----------------------
    # LANGCHAIN TOOL METHODS (string compatible)
    # -----------------------
    @tool(description="Fetch the location of the user based on their IP address (string input, IP optional). Accepts an IP address as a string or empty for current user.")
    async def get_location(self, ipAddress: str = "") -> str:
        return await self._get_location_raw(ipAddress)

    @tool(description="Fetch the current weather for a given city (string input). Accepts a city name as a string.")
    async def get_weather(self, city: str) -> dict:
        return await self._get_weather_raw(city)

    @tool(description="Fetch the current weather based on the user's IP address (string input, IP optional). Accepts an IP address as a string or empty for current user.")
    async def get_weather_by_ip(self, ipAddress: str = "") -> dict:
        city = await self._get_location_raw(ipAddress)
        if city:
            return await self._get_weather_raw(city)
        return {}

    @tool(description="Fetch movie information by title (string input). Accepts a movie title as a string.")
    async def get_movie_info(self, title: str) -> dict:
        return await self._get_movie_info_raw(title)

    @tool(description="Fetch anime information by title (string input). Accepts an anime title as a string.")
    async def get_anime_info(self, title: str) -> dict:
        return await self._get_anime_info_raw(title)
