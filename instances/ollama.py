"""Comunicação local com o servidor Ollama, sem dependências da interface."""

import json
import threading
from collections.abc import Callable, Iterator
from gettext import gettext as _

import requests

from .config import OLLAMA_URL


class OllamaError(RuntimeError):
    """Falha no contrato HTTP ou nos dados retornados pelo servidor."""


def erro_da_resposta(resposta: requests.Response) -> str:
    """Converte um erro HTTP do Ollama em uma mensagem legivel."""
    try:
        detalhe = resposta.json().get("error")
    except (ValueError, AttributeError):
        detalhe = None

    if detalhe:
        return str(detalhe)
    return _("O servidor respondeu com HTTP %s") % resposta.status_code


def listar_modelos() -> list[str]:
    """Lista os modelos instalados que podem completar mensagens."""
    resposta = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
    if not resposta.ok:
        raise OllamaError(erro_da_resposta(resposta))

    dados = resposta.json()
    if not isinstance(dados, dict) or not isinstance(dados.get("models"), list):
        raise OllamaError(_("O servidor retornou uma lista de modelos inválida"))

    modelos = []
    for item in dados["models"]:
        if not isinstance(item, dict):
            continue
        nome = item.get("name")
        capacidades = item.get("capabilities")
        if isinstance(nome, str) and nome and (
            not capacidades or "completion" in capacidades
        ):
            modelos.append(nome)
    return sorted(modelos, key=str.casefold)


def baixar_modelo(
    nome: str, progresso: Callable[[str, float | None], None]
) -> None:
    """Baixa um modelo pela API local e informa status e fração concluída."""
    with requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"name": nome, "stream": True},
        stream=True,
        timeout=(10, 300),
    ) as resposta:
        if not resposta.ok:
            raise OllamaError(erro_da_resposta(resposta))
        for linha in resposta.iter_lines(chunk_size=1, decode_unicode=True):
            if not linha:
                continue
            dados = json.loads(linha)
            if not isinstance(dados, dict):
                raise OllamaError(_("O servidor retornou progresso inválido"))
            if dados.get("error"):
                raise OllamaError(str(dados["error"]))
            total, concluido = dados.get("total"), dados.get("completed")
            fracao = None
            if (
                isinstance(total, (int, float)) and total > 0
                and isinstance(concluido, (int, float))
            ):
                fracao = max(0.0, min(1.0, concluido / total))
            progresso(str(dados.get("status", _("Baixando…"))), fracao)


class OllamaClient:
    """Mantém o estado da requisição de chat para permitir interrupção."""

    def __init__(self):
        self.cancelar = threading.Event()
        self.resposta_ativa = None

    def iniciar(self) -> None:
        self.cancelar.clear()

    def parar(self, worker: Callable[[Callable[[], None]], None] | None = None) -> None:
        """Captura a resposta atual antes de agendar seu fechamento."""
        self.cancelar.set()
        resposta = self.resposta_ativa
        if resposta is None:
            return

        def close():
            try:
                resposta.close()
            except (OSError, AttributeError):
                # O leitor pode estar fechando o mesmo fluxo simultaneamente.
                pass

        if worker is None:
            close()
        else:
            worker(close)

    def iterar_resposta(
        self, modelo: str, mensagens: list[dict[str, str]]
    ) -> Iterator[str]:
        """Produz os fragmentos de texto recebidos da API de chat."""
        if self.cancelar.is_set():
            return
        try:
            with requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": modelo, "messages": mensagens, "stream": True},
                stream=True,
                timeout=(10, 300),
            ) as resposta:
                self.resposta_ativa = resposta
                if self.cancelar.is_set():
                    return
                if not resposta.ok:
                    raise OllamaError(erro_da_resposta(resposta))

                for linha in resposta.iter_lines(chunk_size=1, decode_unicode=True):
                    if self.cancelar.is_set():
                        return
                    if not linha:
                        continue
                    dados = json.loads(linha)
                    if not isinstance(dados, dict):
                        raise OllamaError(
                            _("O servidor retornou um fragmento inválido")
                        )
                    if dados.get("error"):
                        raise OllamaError(str(dados["error"]))
                    mensagem = dados.get("message")
                    if not isinstance(mensagem, dict):
                        raise OllamaError(
                            _("O servidor retornou uma mensagem inválida")
                        )
                    fragmento = mensagem.get("content", "")
                    if not isinstance(fragmento, str):
                        raise OllamaError(_("O servidor retornou texto inválido"))
                    if fragmento:
                        yield fragmento
        except (requests.RequestException, OSError, AttributeError):
            # Fechar a resposta durante iter_lines pode levantar erros internos
            # do requests/urllib3; nesse caso o cancelamento já foi solicitado.
            if not self.cancelar.is_set():
                raise
        finally:
            self.resposta_ativa = None
