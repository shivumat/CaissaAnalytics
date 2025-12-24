from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    api_title: str = "CaissaAnalytics"
    api_description: str = "Chess game analysis service"
    api_version: str = "0.1.0"
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./caissa_analytics.db"
    
    # Stockfish settings
    stockfish_path: str = "/usr/games/stockfish"
    stockfish_depth: int = 20
    stockfish_time_limit: float = 0.1
    
    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_batch_size: int = 10
    
    # Analysis settings
    max_pgns_per_request: int = 100
    mistake_threshold: int = 100  # centipawns
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
