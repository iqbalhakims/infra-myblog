from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    kubeconfig: str = ""  # empty = in-cluster
    pd_token: str
    pd_service_id: str
    pd_infra_escalation_policy_id: str
    slack_token: str
    slack_oncall_channel: str = "#oncall"
    slack_infra_channel: str = "#infra-escalations"
    prometheus_url: str = "http://prometheus:9090"
    chroma_persist_dir: str = "./chroma"
    runbooks_dir: str = "./runbooks"
    model: str = "claude-sonnet-4-6"


settings = Settings()
