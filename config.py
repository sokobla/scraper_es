import yaml
import os


def load_config():
    # Construit un chemin absolu vers config.yml pour éviter les erreurs
    config_path = os.path.join(os.path.dirname(__file__), "config.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_config_with_env_override():
    cfg = load_config()
    # Prioriser la variable d'environnement DATABASE_URL si elle est définie
    if "DATABASE_URL" in os.environ:
        cfg["database"]["url"] = os.environ["DATABASE_URL"]
    return cfg

config = load_config_with_env_override()