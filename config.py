from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://root:root@localhost:3306/doc_insights"
    redis_url: str = "redis://localhost:6379/0"
    max_active_jobs: int = 3
    cache_ttl_seconds: int = 86400

    model_config = {"env_file": ".env"}
