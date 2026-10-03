"""Prévia visual com dados fictícios; nunca acessa Ollama nem systemd.

Use python3 tools/ui_preview.py --empty ou --narrow para inspecionar o layout.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gi

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')
from gi.repository import Adw, Gio

from instances.application import InstancesApplication
from instances.controller import InstancesController
from instances.conversations import Mensagem
from instances.ui.window import InstancesWindow


class PreviewController(InstancesController):
    def verificar(self):
        self.servico_ativo = True
        self.modelos = ['llama3.2:3b', 'gemma3:4b', 'qwen3:8b']
        self.status = 'Conectado • 3 modelos disponíveis'
        self.emit('models-changed')
        self.emit('changed')

    def gerar(self, texto, modelo):
        # As ações de rede permanecem desabilitadas nesta ferramenta visual.
        self.emit('notice', 'Prévia visual: nenhuma mensagem foi enviada ao Ollama')

    def baixar(self, nome):
        self.emit('notice', 'Prévia visual: nenhum modelo será baixado')

    def buscar_modelos(self):
        self.verificar()


class PreviewApplication(InstancesApplication):
    def __init__(self):
        super().__init__()
        self.set_flags(Gio.ApplicationFlags.NON_UNIQUE)

    def do_activate(self):
        window = InstancesWindow(self, PreviewController())
        if '--empty' not in sys.argv:
            previous = window.controller.nova_conversa('gemma3:4b')
            previous.titulo = 'Ideias para um projeto'
            window.sidebar.adicionar_conversa(previous)
            conversa = window.controller.nova_conversa('llama3.2:3b')
            conversa.titulo = 'Aprendendo libadwaita'
            conversa.mensagens = [
                Mensagem(True, 'Como posso começar a criar um aplicativo para o GNOME?'),
                Mensagem(False, 'Comece com uma ideia pequena e um fluxo claro.\n\n'
                         'Uma janela com Adw.ApplicationWindow, uma Adw.HeaderBar '
                         'e uma área de conteúdo já é um bom primeiro passo.\n\n'
                         'Depois, use componentes nativos para navegação, preferências '
                         'e feedback. Assim você mantém a aparência e o comportamento '
                         'consistentes com o GNOME.'),
            ]
            conversa.ultima_resposta = conversa.mensagens[-1].texto
            window.sidebar.adicionar_conversa(conversa)
            window._present_conversation()
        window.sidebar.atualizar_titulos()
        if '--narrow' in sys.argv:
            window.set_default_size(390, 720)
        if '--dark' in sys.argv:
            self.get_style_manager().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        window.present()


raise SystemExit(PreviewApplication().run([sys.argv[0]]))
