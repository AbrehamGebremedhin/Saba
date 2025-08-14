import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class Settings(BaseSettings):
	# Application settings
	APP_NAME: str = Field(default="Saba App", description="Application name")
	DEBUG: bool = Field(default=False, description="Enable debug mode")
	ENV: str = Field(default="development", description="Environment (development, staging, production)")

	# API Keys
	WEATHER_API_KEY: str = Field(default_factory=lambda: os.getenv('WEATHER_API_KEY', ''), description="Weather API Key")
	OMDB_API_KEY: str = Field(default_factory=lambda: os.getenv('OMDB_API_KEY', ''), description="OMDB API Key")
	IPINFO_KEY: str = Field(default_factory=lambda: os.getenv('IPINFO_KEY', ''), description="IPInfo API Key")
	MAL_API_CLIENT_ID: str = Field(default_factory=lambda: os.getenv('MAL_API_CLIENT_ID', ''), description="MyAnimeList API Client ID")

	class Config:
		env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
		env_file_encoding = 'utf-8'

# Instantiate settings
settings = Settings()
