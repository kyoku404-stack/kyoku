from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "KEEP Enterprise Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change_this_secret_key_in_production"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
