"""Central configuration for the legislative data pipeline.

Uses pydantic-settings to load from environment variables with sensible defaults
for local development (DuckDB). Switch to Snowflake by setting WAREHOUSE_BACKEND=snowflake
and providing connection credentials.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"


class CaptureSettings(BaseSettings):
    """Settings for the data capture layer."""

    model_config = {"env_prefix": "CAPTURE_"}

    base_url_diputados: str = "https://sitl.diputados.gob.mx"
    base_url_senado: str = "https://www.senado.gob.mx"
    base_url_sil: str = "https://sil.gobernacion.gob.mx"
    dipmex_repo_url: str = (
        "https://raw.githubusercontent.com/emagar/dipMex/master"
    )
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    rate_limit_delay: float = 1.0
    output_dir: Path = RAW_DIR
    user_agent: str = (
        "MexLegislativePipeline/0.1 (academic research; "
        "github.com/MarioCasanovacf/Portfolio)"
    )


class WarehouseSettings(BaseSettings):
    """Settings for the data warehouse backend."""

    model_config = {"env_prefix": "WAREHOUSE_"}

    backend: Literal["duckdb", "snowflake"] = "duckdb"
    duckdb_path: Path = DATA_DIR / "legislative.duckdb"

    # Snowflake settings (only used when backend=snowflake)
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_database: str = "LEGISLATIVE_MX"
    snowflake_schema: str = "RAW"
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_role: str = "TRANSFORM_ROLE"


class PipelineSettings(BaseSettings):
    """Top-level pipeline configuration."""

    model_config = {"env_prefix": "PIPELINE_"}

    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    capture: CaptureSettings = Field(default_factory=CaptureSettings)
    warehouse: WarehouseSettings = Field(default_factory=WarehouseSettings)


def get_settings() -> PipelineSettings:
    """Load and return pipeline settings from environment."""
    return PipelineSettings()
