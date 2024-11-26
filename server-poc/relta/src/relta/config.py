from typing import Type
from pathlib import Path
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)
from pydantic import Field
from dotenv import load_dotenv

load_dotenv("./.env")  # TODO: find a better solution


class Configuration(BaseSettings):
    """Configuration class for Relta

    Any attributes ending with `_dir_path` will be created when a `Client` object is initialized.

    """

    # Unfortunately, default values cannot be `None`, so you will have to add some extra logic when using config variables that are optional.

    model_config = SettingsConfigDict(
        toml_file="relta.toml",
        pyproject_toml_table_header=("tool", "relta"),
        env_file=".env",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
            PyprojectTomlConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    relta_dir_path: Path = Path(".relta")
    relta_semantic_layer_dir_path: Path = relta_dir_path / "semantic_layer"
    transient_data_dir_path: Path = relta_dir_path / "data"
    relta_internal_path: Path = relta_dir_path / "relta_internal.duckdb"
    relta_data_path: Path = relta_dir_path / "relta_data.duckdb"
    chat_memory_path: Path = relta_dir_path / "chat_memory.sqlite"
    semantic_memory_path: Path = relta_dir_path / "semantic_memory.sqlite"
    storage_path: Path = relta_dir_path / "relta.sqlite"
    storage_table: str = "messages"
    storage_session_id_field: str = "session_id"
    openai_key: str = Field(alias="OPENAI_API_KEY")

    debug: bool = False  # TODO: Further implement debug mode.
    anonymized_telemetry: bool = True
    low_cardinality_cutoff: int = 100

    github_token: str = Field(alias="GITHUB_TOKEN", default="")
    github_repo: str = Field(alias="GITHUB_REPO", default="")
    github_base_branch: str = Field(alias="GITHUB_BASE_BRANCH", default="")

    logfire_token: str = Field(alias="LOGFIRE_TOKEN", default="")
