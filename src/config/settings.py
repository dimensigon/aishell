"""Settings and configuration management."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os


@dataclass
class Settings:
    """Application settings."""

    # Database settings
    db_host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    db_port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    db_name: str = field(default_factory=lambda: os.getenv('DB_NAME', 'postgres'))
    db_user: str = field(default_factory=lambda: os.getenv('DB_USER', 'postgres'))
    db_password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))

    # AI settings
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    model_name: str = field(default_factory=lambda: os.getenv('MODEL_NAME', 'gpt-4'))

    # Vector settings
    vector_dimension: int = 384

    # Panel settings
    max_enrichment_workers: int = 4

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'db_host': self.db_host,
            'db_port': self.db_port,
            'db_name': self.db_name,
            'db_user': self.db_user,
            'vector_dimension': self.vector_dimension,
            'max_enrichment_workers': self.max_enrichment_workers,
            'log_level': self.log_level,
            'model_name': self.model_name
        }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
