from dotenv import load_dotenv
from pathlib import Path
import os
import json
import threading

# Cargar .env una sola vez
load_dotenv()

# Acceso a config.json
_CONFIG_FILE = Path(__file__).parent.parent / "config.json"
_config_lock = threading.Lock()

def get_env(var_name, default=None):
    """Lee variables desde .env"""
    return os.getenv(var_name, default)

def load_config_json():
    """Carga config.json completo"""
    with _config_lock:
        with open(_CONFIG_FILE, "r") as f:
            return json.load(f)

def get_config_value(key, default=None):
    """Accede a un valor específico del config.json"""
    config = load_config_json()
    return config.get(key, default)

def set_config_value(key, value):
    """Actualiza un valor en config.json"""
    with _config_lock:
        config = load_config_json()
        config[key] = value
        with open(_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)