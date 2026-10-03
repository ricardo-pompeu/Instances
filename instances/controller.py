"""Estado da aplicação e operações assíncronas, sem referências a widgets."""

import logging
import threading
from gettext import gettext as _, ngettext
from typing import Callable

from gi.repository import GLib, GObject

from .conversations import Conversa, Mensagem
from .ollama import OllamaClient, baixar_modelo, listar_modelos
from .service import garantir_servico_ollama

LOGGER = logging.getLogger(__name__)


def start_worker(callback: Callable[[], None]) -> None:
    """Executa uma operação fora da thread principal."""
    threading.Thread(target=callback, daemon=True).start()


class InstancesController(GObject.Object):
    """Coordena a sessão; emite sinais apenas na thread principal."""

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'models-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'message-added': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'message-updated': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'notice': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, client=None, dispatch=None, worker=None):
        super().__init__()
        self.client = client if client is not None else OllamaClient()
        self._dispatch = dispatch if dispatch is not None else GLib.idle_add
        self._worker = worker if worker is not None else start_worker
        self.conversas: list[Conversa] = []
        self.conversa_atual: Conversa | None = None
        self.modelos: list[str] = []
        self.servico_ativo = False
        self.verificando = False
        self.carregando_modelos = False
        self.gerando = False
        self.interrompendo = False
        self.baixando = False
        self.status = _("Verificando o serviço…")
        self.download_status = ""
        self.download_fraction: float | None = None
        self._closed = False
        self._generation = 0
        self._refresh_pending = False

    def _notify(self) -> None:
        self.emit('changed')

    def _later(self, callback, *args) -> None:
        def deliver():
            if not self._closed:
                callback(*args)
            return False
        self._dispatch(deliver)

    def nova_conversa(self, modelo: str | None = None) -> Conversa:
        if self.gerando:
            raise RuntimeError(
                _("Interrompa a geração antes de iniciar outra conversa")
            )
        conversa = Conversa(modelo=modelo)
        self.conversas.insert(0, conversa)
        self.conversa_atual = conversa
        return conversa

    def selecionar(self, conversa: Conversa) -> None:
        if not self.gerando:
            self.conversa_atual = conversa

    def verificar(self) -> None:
        if self._closed or self.verificando:
            return
        self.verificando = True
        self.status = _("Verificando e iniciando o serviço, se necessário…")
        self._notify()

        def run():
            try:
                ativo, mensagem = garantir_servico_ollama()
            except Exception as exc:
                LOGGER.exception("Falha ao verificar o serviço")
                ativo, mensagem = False, str(exc)
            self._later(self._servico_verificado, ativo, mensagem)
        self._worker(run)

    def _servico_verificado(self, ativo: bool, mensagem: str) -> None:
        self.verificando = False
        self.servico_ativo = ativo
        self.status = mensagem
        if ativo:
            self.buscar_modelos()
        else:
            self.modelos = []
            self.emit('models-changed')
            self.emit('notice', mensagem)
        self._notify()

    def buscar_modelos(self) -> None:
        if self._closed or self.carregando_modelos:
            return
        if self.gerando:
            self._refresh_pending = True
            return
        if not self.servico_ativo:
            self.verificar()
            return
        self.carregando_modelos = True
        self.status = _("Carregando modelos instalados…")
        self._notify()

        def run():
            try:
                modelos, erro = listar_modelos(), None
            except Exception as exc:
                LOGGER.exception("Falha ao listar modelos")
                modelos, erro = [], str(exc)
            self._later(self._modelos_carregados, modelos, erro)
        self._worker(run)

    def _modelos_carregados(self, modelos: list[str], erro: str | None) -> None:
        self.carregando_modelos = False
        self.modelos = modelos
        if erro:
            self.status = _("Falha ao carregar os modelos")
            self.emit('notice', _("Não foi possível listar os modelos: %s") % erro)
        else:
            self.status = ngettext(
                "Conectado • %s modelo disponível",
                "Conectado • %s modelos disponíveis", len(modelos),
            ) % len(modelos)
        self.emit('models-changed')
        self._notify()

    def baixar(self, nome: str) -> None:
        nome = nome.strip()
        if not nome or any(char.isspace() for char in nome):
            raise ValueError(_("Digite um nome de modelo válido"))
        if self._closed or self.baixando or not self.servico_ativo:
            raise RuntimeError(_("O servidor deve estar conectado e livre para baixar"))
        self.baixando = True
        self.download_fraction = None
        self.download_status = _("Baixando %s…") % nome
        self._notify()

        def run():
            try:
                baixar_modelo(nome, lambda status, fraction: self._later(
                    self._download_progress, nome, status, fraction
                ))
                erro = None
            except Exception as exc:
                LOGGER.exception("Falha no download")
                erro = str(exc)
            self._later(self._download_finished, nome, erro)
        self._worker(run)

    def _download_progress(self, nome, status, fraction) -> None:
        self.download_fraction = fraction
        percent = f" • {fraction:.0%}" if fraction is not None else ""
        self.download_status = f"{nome}: {status}{percent}"
        self._notify()

    def _download_finished(self, nome, erro) -> None:
        self.baixando = False
        self.download_fraction = None
        self.download_status = ""
        if erro:
            self.emit('notice', _("Não foi possível baixar %(nome)s: %(erro)s") % {
                'nome': nome, 'erro': erro,
            })
        else:
            self.emit('notice', _("Modelo %s baixado") % nome)
            self.buscar_modelos()
        self._notify()

    def gerar(self, texto: str, modelo: str) -> None:
        if self._closed or self.gerando:
            return
        if (
            not self.servico_ativo or self.carregando_modelos
            or modelo not in self.modelos
        ):
            raise RuntimeError(_("Selecione um modelo disponível antes de enviar"))
        if not texto.strip():
            raise ValueError(_("Digite uma mensagem antes de enviar"))
        conversa = self.conversa_atual
        if conversa is None:
            raise RuntimeError(_("Selecione uma conversa"))
        pergunta = Mensagem(usuario=True, texto=texto.strip())
        resposta = Mensagem(usuario=False, texto=_("Pensando…"))
        conversa.modelo = modelo
        conversa.nomear_pela_primeira_mensagem(pergunta.texto)
        conversa.historico.append({'role': 'user', 'content': pergunta.texto})
        conversa.mensagens.extend((pergunta, resposta))
        conversa.ultima_resposta = ""
        mensagens = [dict(item) for item in conversa.historico]
        self._generation += 1
        generation = self._generation
        self.gerando = True
        self.interrompendo = False
        self.client.iniciar()
        self.status = _("Gerando com %s…") % modelo
        self.emit('message-added', pergunta)
        self.emit('message-added', resposta)
        self._notify()

        def run():
            partes = []
            erro = None
            try:
                for fragmento in self.client.iterar_resposta(modelo, mensagens):
                    partes.append(fragmento)
                    self._later(self._fragment, generation, resposta, fragmento,
                                len(partes) == 1)
            except Exception as exc:
                if not self.client.cancelar.is_set():
                    LOGGER.exception("Falha na geração")
                    erro = str(exc)
            self._later(self._finished, generation, conversa, resposta,
                        ''.join(partes), erro, self.client.cancelar.is_set())
        self._worker(run)

    def _fragment(self, generation, resposta, fragmento, primeiro) -> None:
        if generation != self._generation:
            return
        resposta.texto = fragmento if primeiro else resposta.texto + fragmento
        self.emit('message-updated', resposta)

    def _finished(self, generation, conversa, resposta, texto, erro, cancelado) -> None:
        if generation != self._generation:
            return
        self.gerando = False
        self.interrompendo = False
        if cancelado:
            prefix = texto + '\n\n' if texto else ''
            resposta.texto = prefix + _("Geração interrompida.")
            self.status = _("Geração interrompida")
        elif erro:
            resposta.texto = _("Não foi possível gerar a resposta.\n\n%s") % erro
            self.status = _("Falha durante a geração")
            self.emit('notice', _("Erro do Ollama: %s") % erro)
        elif texto:
            resposta.texto = texto
            conversa.historico.append({'role': 'assistant', 'content': texto})
            conversa.ultima_resposta = texto
            self.status = _("Conectado • resposta concluída")
        else:
            resposta.texto = _("O modelo terminou sem retornar texto.")
            self.status = _("Conectado • resposta concluída")
        self.emit('message-updated', resposta)
        self._notify()
        if self._refresh_pending:
            self._refresh_pending = False
            self.buscar_modelos()

    def parar(self) -> None:
        if not self.gerando or self.interrompendo:
            return
        self.interrompendo = True
        self.client.cancelar.set()
        self.status = _("Interrompendo a geração…")
        # close() pode aguardar uma leitura HTTP; nunca bloquear a interface.
        self.client.parar(self._worker)
        self._notify()

    def fechar(self) -> None:
        """Invalida callbacks pendentes e solicita o término da geração."""
        if self._closed:
            return
        self._closed = True
        self._generation += 1
        self.client.cancelar.set()
        self.client.parar(self._worker)
