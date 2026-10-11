from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    github_token: str = ""
    service_api_key: str = ""
    agent_model: str = "claude-sonnet-5-5"
    sandbox: str = "docker"  # docker | local
    max_fix_attempts: int = 3

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
