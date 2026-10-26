from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada del bot validada por Pydantic."""

    # Meta WhatsApp Cloud API
    META_APP_SECRET: str = "local_dev_app_secret"
    META_VERIFY_TOKEN: str = "local_dev_verify_token"
    META_ACCESS_TOKEN: str = "local_dev_access_token"
    META_PHONE_NUMBER_ID: str = "1234567890"
    GRAPH_API_VERSION: str = "v26.0"

    # Upstash Redis (Serverless REST API)
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # Control de Cupo y Reglas de Negocio
    LIMITE_MENSUAL: int = 1000
    UMBRAL_CORTE: int = 950
    PERMITIR_EMERGENCIAS_TRAS_CORTE: bool = True
    TIMEZONE: str = "America/Caracas"

    # Servidor y Alertas
    PORT: int = 8000
    ALERT_EMAIL: str = ""

    # Gateway WhatsApp Web (QR / Baileys)
    GATEWAY_URL: str = "http://localhost:3001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
