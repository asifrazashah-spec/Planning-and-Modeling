"""Configuration management."""

import os
from typing import Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class DatabaseConfig:
    """Database configuration."""

    driver: str = "postgresql"
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 5432))
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "password")
    database: str = os.getenv("DB_NAME", "tpms")

    def connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis cache configuration."""

    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6379))
    db: int = int(os.getenv("REDIS_DB", 0))

    def connection_string(self) -> str:
        """Get Redis connection string."""
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class APIConfig:
    """API configuration."""

    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", 8000))
    workers: int = int(os.getenv("API_WORKERS", 4))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


@dataclass
class SimulationConfig:
    """Simulation configuration."""

    timestep: float = 0.1  # seconds
    random_seed: int = 42
    max_vehicles: int = 100000
    enable_emissions: bool = True


@dataclass
class ModelConfig:
    """Model parameters."""

    # 4-step model
    trip_generation_rates: Dict = None
    attraction_rates: Dict = None
    gravity_decay: float = 0.05

    # Assignment
    bpr_alpha: float = 0.15
    bpr_beta: float = 4.0
    assignment_iterations: int = 100
    convergence_gap: float = 0.01

    # Accessibility
    accessibility_decay: float = 0.05
    accessibility_threshold: float = 60  # minutes

    def __post_init__(self):
        """Set defaults."""
        if self.trip_generation_rates is None:
            self.trip_generation_rates = {
                "work": 0.5,
                "school": 0.3,
                "other": 0.2,
            }
        if self.attraction_rates is None:
            self.attraction_rates = {
                "work": 0.5,
                "school": 0.3,
                "other": 0.2,
            }


class Config:
    """Main configuration class."""

    def __init__(self):
        """Initialize configuration."""
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.api = APIConfig()
        self.simulation = SimulationConfig()
        self.model = ModelConfig()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "workers": self.api.workers,
                "debug": self.api.debug,
            },
            "simulation": {
                "timestep": self.simulation.timestep,
                "random_seed": self.simulation.random_seed,
            },
        }


# Global config instance
config = Config()
