"""Configuration management."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Model selection - gpt-4o-mini is 3-5x faster and much cheaper
    # Use gpt-4o for complex reasoning, gpt-4o-mini for speed
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    
    # Agent settings - higher turns allows finding more leads
    MAX_TURNS: int = int(os.getenv("MAX_TURNS", "20"))
    
    # Default search parameters
    DEFAULT_SEARCH_RADIUS: int = 25  # miles
    DEFAULT_YEAR_THRESHOLD: int = 2005
    DEFAULT_LEAD_COUNT: int = int(os.getenv("DEFAULT_LEAD_COUNT", "10"))
    
    @classmethod
    def validate(cls) -> bool:
        """Check required config is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True


config = Config()

