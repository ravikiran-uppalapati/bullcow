import os


ENV_MAPPING = {
    "google_api_key": "GOOGLE_API_KEY",
    "langsmith_api_key": "LANGSMITH_API_KEY",
    "langsmith_project": "LANGSMITH_PROJECT",
    "langsmith_endpoint": "LANGSMITH_ENDPOINT",
}


def apply_runtime_config(config: dict) -> None:
    for config_key, env_key in ENV_MAPPING.items():
        value = str(config.get(config_key, "")).strip()
        if value:
            os.environ[env_key] = value

    if str(config.get("langsmith_api_key", "")).strip():
        os.environ["LANGSMITH_TRACING"] = "true"
