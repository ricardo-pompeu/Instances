"""Verificação e inicialização do serviço local do Ollama."""

import shutil
import subprocess
import time
from gettext import gettext as _

import requests

from .config import OLLAMA_URL

OLLAMA_SERVICE = "ollama.service"


def ollama_esta_disponivel() -> bool:
    """Retorna se a API do Ollama esta pronta para receber requisicoes."""
    try:
        resposta = requests.get(OLLAMA_URL, timeout=2)
        return resposta.status_code == 200
    except requests.RequestException:
        return False


def garantir_servico_ollama() -> tuple[bool, str]:
    """Inicia o servico usando a autorizacao grafica do PolicyKit."""
    if ollama_esta_disponivel():
        return True, _("Servidor conectado")

    if not shutil.which("ollama"):
        return False, _("O Ollama não está instalado")

    if not shutil.which("systemctl"):
        return False, _("Este sistema não oferece suporte ao systemd")

    try:
        resultado = subprocess.run(
            ["systemctl", "start", OLLAMA_SERVICE],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, _("A autorização para iniciar o Ollama expirou")
    except OSError as erro:
        return False, _("Não foi possível iniciar o serviço: %s") % erro

    if resultado.returncode != 0:
        detalhe = (resultado.stderr or resultado.stdout).strip()
        detalhe = detalhe.splitlines()[-1] if detalhe else ""
        detalhe_normalizado = detalhe.lower()

        if (
            "authentication" in detalhe_normalizado
            or "access denied" in detalhe_normalizado
        ):
            return False, _("A autorização para iniciar o Ollama foi recusada")
        if "not found" in detalhe_normalizado:
            return False, _("O serviço Ollama não foi encontrado neste sistema")
        if detalhe:
            return False, _("Não foi possível iniciar o Ollama: %s") % detalhe
        return False, _("Não foi possível iniciar o Ollama. Verifique a autorização")

    for tentativa in range(12):
        if ollama_esta_disponivel():
            return True, _("Servidor conectado")
        time.sleep(0.5)

    return False, _("O serviço iniciou, mas a API do Ollama não respondeu")
