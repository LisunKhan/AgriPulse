from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AgriPulse API"
    database_url: str = "postgresql://postgres:password123@localhost:5432/agripulse"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "agripulse/telemetry/#"
    temp_min_c: float = 2.0
    temp_max_c: float = 8.0
    humidity_min_pct: float = 40.0
    humidity_max_pct: float = 90.0
    alert_cooldown_sec: int = 60


settings = Settings()
