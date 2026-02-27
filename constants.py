import os
from pathlib import Path

APP_NAME = "Knowledgedock"
APP_DIR_NAME = ".knowledgedock"

# Base Data Directory
DATA_DIR = Path.home() / APP_DIR_NAME

# Subdirectories
DOWNLOADS_DIR = DATA_DIR / "downloads"
EXTENSIONS_DIR = DATA_DIR / "extensions"
LOGS_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "knowledgedock.db"
SETTINGS_PATH = DATA_DIR / "settings.json"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)
EXTENSIONS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
