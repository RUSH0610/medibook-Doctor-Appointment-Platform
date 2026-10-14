from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/medibook"
    jwt_secret: str = "development-only-change-this-secret-32-characters"
    access_token_minutes: int = 30
    frontend_origin: str = "http://localhost:5173"
    upload_directory: str = "local_uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    doctor_email: str = "doctor@example.com"
    doctor_password: str = ""
    doctor_name: str = "Dr. Demo"
    doctor_specialization: str = "General Medicine"
    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = "MediBook Admin"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
