"""Verifica templates, navegação e streaming sem acessar Ollama ou systemd."""

import threading
import time

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

if not Gtk.init_check() or Gdk.Display.get_default() is None:
    print('Sem display: teste GTK ignorado')
    raise SystemExit(77)

from instances.application import InstancesApplication
from instances.controller import InstancesController
from instances.config import APP_ID
from instances.ui.download_dialog import DownloadDialog
from instances.ui.window import InstancesWindow


class OfflineController(InstancesController):
    def verificar(self):
        pass


class FakeClient:
    def __init__(self):
        self.cancelar = threading.Event()

    def iniciar(self):
        self.cancelar.clear()

    def parar(self, worker=None):
        self.cancelar.set()

    def iterar_resposta(self, model, messages):
        yield 'resposta simulada'


def drain():
    context = GLib.MainContext.default()
    deadline = time.monotonic() + 0.15
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.005)


app = InstancesApplication()
app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
app.register(None)
jobs = []
controller = OfflineController(client=FakeClient(), worker=jobs.append)
window = InstancesWindow(app, controller)
window.present()
dialog = DownloadDialog(controller, lambda text: None)
dialog.present(window)
drain()
assert controller.conversa_atual is not None
assert window.divisao.get_sidebar() is window.sidebar
assert isinstance(window.sidebar.navigation, Adw.Sidebar)
assert Gtk.IconTheme.get_for_display(window.get_display()).has_icon(APP_ID)
assert Gtk.IconTheme.get_for_display(window.get_display()).has_icon(APP_ID + '-symbolic')
assert window.botao_enviar.get_icon_name() == 'go-up-symbolic'
assert Gtk.IconTheme.get_for_display(window.get_display()).has_icon('go-up-symbolic')
assert not window.lookup_action('enviar').get_enabled()
assert dialog.entry is not None
dialog.entry.set_text('nome com espaços')
assert not dialog.get_response_enabled('baixar')
dialog.entry.set_text('llama3.2:1b')
assert dialog.get_response_enabled('baixar')
dialog.close()
controller.servico_ativo = True
controller.modelos = ['modelo', 'outro']
controller.emit('models-changed')
controller.emit('changed')
first = controller.conversa_atual
window.combo.set_selected(1)
window.prompt.get_buffer().set_text('rascunho da primeira')
window.nova_conversa()
assert window.caixa_mensagens.get_first_child() is None
assert window._prompt_text() == ''
second = controller.conversa_atual
window.prompt.get_buffer().set_text('rascunho da segunda')
window._selecionar(window.sidebar, first)
assert window._prompt_text() == 'rascunho da primeira'
assert window._modelo_selecionado() == 'outro'
window._selecionar(window.sidebar, second)
assert window._prompt_text() == 'rascunho da segunda'
window.prompt.get_buffer().set_text('primeira pergunta')
assert window.lookup_action('enviar').get_enabled()
window.executar_modelo()
assert not window.lookup_action('enviar').get_enabled()
assert not window.lookup_action('nova-conversa').get_enabled()
controller.parar()
jobs.pop(0)()
drain()
assert not window.lookup_action('parar').get_enabled()
window.prompt.get_buffer().set_text('segunda pergunta')
window.executar_modelo()
jobs.pop(0)()
drain()
assert controller.conversa_atual.ultima_resposta == 'resposta simulada'
assert window.lookup_action('copiar').get_enabled()
# Atualizar modelos não deve sobrescrever o modelo desta conversa.
window.combo.set_selected(1)
controller.modelos = ['outro', 'modelo']
controller.emit('models-changed')
assert window._modelo_selecionado() == 'outro'
# A desconexão temporária não deve apagar o modelo escolhido.
controller.modelos = []
controller.emit('models-changed')
assert controller.conversa_atual.modelo == 'outro'
controller.modelos = ['outro', 'modelo']
controller.emit('models-changed')
assert window._modelo_selecionado() == 'outro'
controller._download_progress('modelo', 'baixando', 0.4)
controller.baixando = True
controller.emit('changed')
assert window.download_progress.get_fraction() == 0.4
controller.baixando = False
controller.emit('changed')
# Dialogs novos também precisam carregar sem erros GTK.
window._shortcuts()
drain()
window.get_visible_dialog().close()
window._confirmar_limpar()
drain()
confirm = window.get_visible_dialog()
assert confirm.get_default_response() == 'cancelar'
confirm.close()
# Uma janela estreita deve recolher o painel sem impor 560px de largura.
window.close()
narrow = InstancesWindow(app, OfflineController())
narrow.set_default_size(390, 600)
narrow.present()
drain()
assert narrow.divisao.get_collapsed(), (narrow.get_width(), narrow.get_height())
assert narrow.sidebar.navigation.get_mode() == Adw.SidebarMode.PAGE
narrow._buscar_conversas()
assert narrow.divisao.get_show_sidebar()
narrow.sidebar.search_entry.set_text('inexistente')
drain()
filter = narrow.sidebar.navigation.get_filter()
assert filter.get_search() == 'inexistente'
assert not filter.match(narrow.sidebar.navigation.get_item(0))
narrow.nova_conversa()
assert narrow.sidebar.search_entry.get_text() == ''
narrow.close()
print('Templates, rascunhos, modelos, cancelamento, diálogos e adaptação: OK')
