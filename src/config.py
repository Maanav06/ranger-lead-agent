"""Configuration management."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first (for Streamlit Cloud / HuggingFace)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except ImportError:
        pass
    except Exception:
        pass
    
    # Fall back to environment variables
    return os.getenv(key, default)


class Config:
    """Application configuration."""
    
    OPENAI_API_KEY: str = get_secret("OPENAI_API_KEY", "")
    
    # Model selection - gpt-4o-mini is 3-5x faster and much cheaper
    # Use gpt-4o for complex reasoning, gpt-4o-mini for speed
    OPENAI_MODEL: str = get_secret("OPENAI_MODEL", "gpt-4o-mini")
    
    OUTPUT_DIR: str = get_secret("OUTPUT_DIR", "output")
    
    # Agent settings - higher turns allows finding more leads (50 for complex searches)
    MAX_TURNS: int = int(get_secret("MAX_TURNS", "50"))
    
    # Default search parameters
    DEFAULT_SEARCH_RADIUS: int = 25  # miles
    DEFAULT_YEAR_THRESHOLD: int = 2005
    DEFAULT_LEAD_COUNT: int = int(get_secret("DEFAULT_LEAD_COUNT", "10"))
    
    @classmethod
    def validate(cls) -> bool:
        """Check required config is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True


config = Config()

