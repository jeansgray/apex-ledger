"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    apex_data_dir: Path = Path("./data")
    apex_ledger_db: Path = Path("./data/ledger.db")
    apex_skills_dir: Path = Path("./.cursor/skills")
    apex_skill_manifest: Path = Path("./skills/manifest.json")

    mirofish_base_url: str = "http://127.0.0.1:5001"
    mirofish_default_simulation_id: str = ""
    apex_simulation_cache: Path = Path("./data/simulation_cache.json")
    apex_default_cash_to_deploy: float = 1000.0
    apex_use_live_simulation: bool = True
    apex_use_kronos: bool = True
    kronos_base_url: str = "http://127.0.0.1:5002"
    kronos_forecast_days: int = 30

    llm_api_key: str = ""
    zep_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_name: str = "gpt-4o-mini"

    # Future bank sync (Plaid) — set in .env when ready
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"
    apex_integrations_file: Path = Path("./data/integrations.json")
    apex_public_base_url: str = "http://127.0.0.1:8080"

    schwab_app_key: str = ""
    schwab_app_secret: str = ""
    schwab_callback_url: str = ""

    @property
    def schwab_redirect_uri(self) -> str:
        if self.schwab_callback_url:
            return self.schwab_callback_url
        return f"{self.apex_public_base_url.rstrip('/')}/oauth/schwab/callback"

    def ensure_dirs(self) -> None:
        self.apex_data_dir.mkdir(parents=True, exist_ok=True)
        self.apex_skills_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
