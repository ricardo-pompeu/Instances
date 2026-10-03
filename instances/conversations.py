"""Estado das conversas mantido em memória durante a sessão."""

from dataclasses import dataclass, field
from gettext import gettext as _


@dataclass
class Mensagem:
    usuario: bool
    texto: str


@dataclass
class Conversa:
    titulo: str = field(default_factory=lambda: _("Nova conversa"))
    historico: list[dict[str, str]] = field(default_factory=list)
    mensagens: list[Mensagem] = field(default_factory=list)
    ultima_resposta: str = ""
    modelo: str | None = None
    rascunho: str = ""

    def nomear_pela_primeira_mensagem(self, texto: str) -> None:
        if self.titulo != _("Nova conversa"):
            return
        primeira_linha = texto.splitlines()[0]
        self.titulo = primeira_linha[:36] + ("…" if len(primeira_linha) > 36 else "")

    def limpar(self) -> None:
        self.titulo = _("Nova conversa")
        self.historico.clear()
        self.mensagens.clear()
        self.ultima_resposta = ""
        self.rascunho = ""
