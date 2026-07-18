import json
import os
import logging
from src.config import CONFIG_PATH

logger = logging.getLogger(__name__)


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding='utf-8') as file:
            json.dump({}, file)
        return {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            logger.warning(f"Ошибка чтения файла по пути {CONFIG_PATH}")
            return {}


def save_config(config: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)
