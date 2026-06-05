"""Configuration management for JIRA Activity Agent."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # JIRA Configuration
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_USERNAME: str = os.getenv("JIRA_USERNAME", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "")

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")

    # Agent Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "100"))
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))

    # Server Configuration
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        required = ["JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        for field in required:
            if not getattr(cls, field, None):
                print(f"Missing required configuration: {field}")
                return False
        return True
