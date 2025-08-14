from pydantic import BaseModel, Field

class LocationSearch(BaseModel):
    ipAddress: str = Field(description="IP address to search for")

class WeatherSearch(BaseModel):
    city: str = Field(description="City name to get the weather for")

class MovieSearch(BaseModel):
    title: str = Field(description="Movie title to search for")

class AnimeSearch(BaseModel):
    title: str = Field(description="Anime title to search for")
