"""Metadados compartilhados entre execução direta e instalação Meson."""

from pathlib import Path

try:
    from ._build_config import APP_ID, DATA_DIR, LOCALE_DIR, VERSION
except ImportError:
    APP_ID = 'com.example.Instances'
    VERSION = '0.1'
    DATA_DIR = str(Path(__file__).resolve().parent.parent / 'data')
    LOCALE_DIR = str(Path(__file__).resolve().parent.parent / 'data' / 'locale')

GETTEXT_DOMAIN = 'instances'
RESOURCE_PREFIX = '/com/example/Instances'
OLLAMA_URL = 'http://127.0.0.1:11434'
