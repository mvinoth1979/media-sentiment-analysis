from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    influxdb_url: str = ""
    influxdb_token: str = ""
    influxdb_org: str = ""
    influxdb_bucket: str = "mediasense"

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "mediasense-raw"

    upstash_redis_host: str = ""
    upstash_redis_port: int = 6379
    upstash_redis_password: str = ""

    gemini_api_key: str = ""
    groq_api_key: str = ""

    secret_key: str = "dev-secret-key"
    environment: str = "development"

settings = Settings()
