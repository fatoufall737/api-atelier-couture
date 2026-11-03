from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ces valeurs viennent du fichier .env, jamais écrites dans le code
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()