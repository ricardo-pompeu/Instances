"""Interface adaptável: widgets nativos, ações e estado da conversa."""

from gettext import gettext as _

from ..config import APP_ID, VERSION
from ..controller import InstancesController
from ..resources import load_styles, template
from gi.repository import Adw, Gio, GLib, Gtk, Pango

from .download_dialog import DownloadDialog
from .sidebar import ConversationSidebar


@template('window')
class InstancesWindow(Adw.ApplicationWindow):
    """A interface apresenta o estado; o controlador executa as operações."""

    __gtype_name__ = 'InstancesWindow'
    toast_overlay = Gtk.Template.Child()
    divisao = Gtk.Template.Child()
    titulo_conversa = Gtk.Template.Child()
    botao_mostrar_sidebar = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    banner_conexao = Gtk.Template.Child()
    download_box = Gtk.Template.Child()
    download_status = Gtk.Template.Child()
    download_progress = Gtk.Template.Child()
    spinner_servico = Gtk.Template.Child()
    combo = Gtk.Template.Child()
    spinner_geracao = Gtk.Template.Child()
    estado_geracao = Gtk.Template.Child()
    pilha_conversa = Gtk.Template.Child()
    pagina_vazia = Gtk.Template.Child()
    sugestoes = Gtk.Template.Child()
    scroll_conversa = Gtk.Template.Child()
    caixa_mensagens = Gtk.Template.Child()
    prompt = Gtk.Template.Child()
    botao_parar = Gtk.Template.Child()
    botao_enviar = Gtk.Template.Child()

    def __init__(self, app, controller=None):
        super().__init__(application=app)
        self.controller = controller if controller is not None else InstancesController()
        self._labels = {}
        self._closed = False
        self._was_generating = False
        self._updating_models = False
        self._loading_draft = False
        self._scroll_pending = False
        self._download_pulse_id = 0
        self._follow_output = True
        load_styles(self.get_display())
        self._actions()
        self.sidebar = ConversationSidebar()
        self.divisao.set_sidebar(self.sidebar)
        self.sidebar.connect('selected', self._selecionar)
        self.combo.connect('notify::selected', self._modelo_alterado)
        self.divisao.connect('notify::show-sidebar', self._sidebar_changed)
        self.divisao.connect('notify::collapsed', self._sidebar_changed)
        self.prompt.get_buffer().connect('changed', self._prompt_changed)
        adjustment = self.scroll_conversa.get_vadjustment()
        adjustment.connect('value-changed', self._scroll_changed)
        self.connect('close-request', self._close)
        self._suggestions()
        self._handlers = [
            self.controller.connect('changed', self._changed),
            self.controller.connect('models-changed', self._modelos),
            self.controller.connect('message-added', self._message_added),
            self.controller.connect('message-updated', self._message_updated),
            self.controller.connect('notice', lambda _c, text: self._toast(text)),
        ]
        self.nova_conversa()
        self._sidebar_changed()
        self.controller.verificar()

    def _actions(self) -> None:
        callbacks = {
            'nova-conversa': self.nova_conversa,
            'enviar': self.executar_modelo,
            'parar': lambda *_: self.controller.parar(),
            'limpar': self._confirmar_limpar,
            'copiar': self.copiar_resposta,
            'baixar-modelo': self._download,
            'atualizar-modelos': lambda *_: self.controller.buscar_modelos(),
            'reconectar': lambda *_: self.controller.verificar(),
            'alternar-sidebar': self._alternar_sidebar,
            'buscar-conversas': self._buscar_conversas,
            'atalhos': self._shortcuts,
            'sobre': self._about,
        }
        for name, callback in callbacks.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', callback)
            self.add_action(action)
        app = self.get_application()
        for action, shortcuts in {
            'nova-conversa': ['<Control>n'],
            'enviar': ['<Control>Return', '<Control>KP_Enter'],
            'parar': ['<Control>period'],
            'alternar-sidebar': ['F9'],
            'buscar-conversas': ['<Control>f'],
            'atalhos': ['<Control>question'],
        }.items():
            app.set_accels_for_action(f'win.{action}', shortcuts)
        menu = Gio.Menu()
        conversations = Gio.Menu()
        conversations.append(_('Nova conversa'), 'win.nova-conversa')
        conversations.append(_('Copiar última resposta'), 'win.copiar')
        conversations.append(_('Limpar conversa…'), 'win.limpar')
        models = Gio.Menu()
        models.append(_('Baixar modelo…'), 'win.baixar-modelo')
        models.append(_('Atualizar modelos'), 'win.atualizar-modelos')
        models.append(_('Reconectar ao Ollama'), 'win.reconectar')
        info = Gio.Menu()
        info.append(_('Atalhos de teclado'), 'win.atalhos')
        info.append(_('About Instances'), 'win.sobre')
        menu.append_section(None, conversations)
        menu.append_section(None, models)
        menu.append_section(None, info)
        self.menu_button.set_menu_model(menu)

    def _suggestions(self) -> None:
        for title, icon, text in (
            (_('Explicar um conceito'), 'dialog-information-symbolic',
             _('Explique de forma simples: ')),
            (_('Resumir um texto'), 'format-justify-left-symbolic',
             _('Resuma o texto a seguir:\n\n')),
            (_('Gerar ideias'), 'starred-symbolic', _('Sugira ideias para: ')),
        ):
            content = Adw.ButtonContent(label=title, icon_name=icon,
                                        halign=Gtk.Align.START)
            button = Gtk.Button(child=content, height_request=44)
            button.add_css_class('suggestion-button')
            button.connect('clicked', lambda _b, value: self._usar_sugestao(value), text)
            self.sugestoes.append(button)

    def _enable(self, name: str, enabled: bool) -> None:
        self.lookup_action(name).set_enabled(enabled)

    def _changed(self, *_args) -> None:
        c = self.controller
        busy_service = c.verificando or c.carregando_modelos
        self.spinner_servico.set_spinning(busy_service)
        self.spinner_servico.set_visible(busy_service)
        self.spinner_geracao.set_spinning(c.gerando)
        self.spinner_geracao.set_visible(c.gerando)
        self.estado_geracao.set_label(c.status if c.gerando else _('Ctrl+Enter para enviar'))
        self.combo.set_subtitle(c.status)
        ready = c.servico_ativo and bool(c.modelos) and not busy_service
        self.combo.set_sensitive(ready and not c.gerando)
        self.botao_parar.set_visible(c.gerando)
        self.botao_enviar.set_visible(not c.gerando)
        self._enable('enviar', ready and not c.gerando and bool(self._prompt_text().strip()))
        self._enable('parar', c.gerando and not c.interrompendo)
        self._enable('nova-conversa', not c.gerando)
        self._enable('limpar', not c.gerando and bool(c.conversa_atual and c.conversa_atual.mensagens))
        self._enable('copiar', bool(c.conversa_atual and c.conversa_atual.ultima_resposta))
        self._enable('atualizar-modelos', not c.gerando and not busy_service)
        self._enable('reconectar', not c.gerando and not busy_service)
        self._enable('baixar-modelo', c.servico_ativo and not c.baixando)
        self.sidebar.set_busy(c.gerando)
        self.sidebar.atualizar_titulos()
        if c.conversa_atual:
            self.titulo_conversa.set_title(c.conversa_atual.titulo)
        self.titulo_conversa.set_subtitle(_('Respondendo…') if c.gerando else _('Instances'))
        connection_problem = not c.servico_ativo and not c.verificando
        no_models = c.servico_ativo and not c.modelos and not busy_service
        self.banner_conexao.set_revealed(connection_problem or no_models)
        if no_models:
            self.banner_conexao.set_title(_('Nenhum modelo instalado'))
            self.banner_conexao.set_button_label(_('Baixar modelo'))
            self.banner_conexao.set_action_name('win.baixar-modelo')
        elif connection_problem:
            self.banner_conexao.set_title(_('Ollama desconectado'))
            self.banner_conexao.set_button_label(_('Reconectar'))
            self.banner_conexao.set_action_name('win.reconectar')
        self.download_box.set_visible(c.baixando)
        self.download_status.set_label(c.download_status)
        if c.baixando and c.download_fraction is not None:
            self._stop_download_pulse()
            self.download_progress.set_fraction(c.download_fraction)
        elif c.baixando and not self._download_pulse_id:
            self._download_pulse_id = GLib.timeout_add(150, self._pulse_download)
        elif not c.baixando:
            self._stop_download_pulse()
        if self._was_generating and not c.gerando:
            self.prompt.grab_focus()
        self._was_generating = c.gerando

    def _pulse_download(self) -> bool:
        self.download_progress.pulse()
        return True

    def _stop_download_pulse(self) -> None:
        if self._download_pulse_id:
            GLib.source_remove(self._download_pulse_id)
            self._download_pulse_id = 0

    def _modelos(self, *_args) -> None:
        c = self.controller
        model = c.conversa_atual.modelo if c.conversa_atual else None
        self._updating_models = True
        try:
            self.combo.set_model(Gtk.StringList.new(c.modelos))
            if model in c.modelos:
                self.combo.set_selected(c.modelos.index(model))
        finally:
            self._updating_models = False
        self._modelo_alterado()

    def _modelo_alterado(self, *_args) -> None:
        model = self._modelo_selecionado()
        if not self._updating_models and self.controller.conversa_atual and model:
            self.controller.conversa_atual.modelo = model

    def _modelo_selecionado(self) -> str | None:
        item = self.combo.get_selected_item()
        return item.get_string() if item else None

    def nova_conversa(self, *_args) -> None:
        try:
            conversa = self.controller.nova_conversa(self._modelo_selecionado())
        except RuntimeError as exc:
            self._toast(str(exc))
            return
        self.sidebar.adicionar_conversa(conversa)
        self._present_conversation()
        self._recolher_sidebar()
        self.prompt.grab_focus()

    def _selecionar(self, _sidebar, conversa) -> None:
        self.controller.selecionar(conversa)
        if self.controller.conversa_atual is not conversa:
            return
        if conversa.modelo in self.controller.modelos:
            self.combo.set_selected(self.controller.modelos.index(conversa.modelo))
        else:
            conversa.modelo = self._modelo_selecionado()
        self._present_conversation()
        self._recolher_sidebar()

    def _present_conversation(self) -> None:
        conversa = self.controller.conversa_atual
        self._limpar_baloes()
        self._follow_output = True
        for mensagem in conversa.mensagens:
            self._message_added(self.controller, mensagem)
        self.pilha_conversa.set_visible_child_name('mensagens' if conversa.mensagens else 'vazio')
        self._loading_draft = True
        try:
            self.prompt.get_buffer().set_text(conversa.rascunho)
        finally:
            self._loading_draft = False
        self._changed()

    def _prompt_text(self) -> str:
        buffer = self.prompt.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)

    def _prompt_changed(self, *_args) -> None:
        if self._loading_draft:
            return
        if self.controller.conversa_atual:
            self.controller.conversa_atual.rascunho = self._prompt_text()
        self._changed()

    def executar_modelo(self, *_args) -> None:
        model = self._modelo_selecionado()
        try:
            if model is None:
                raise ValueError(_('Selecione um modelo antes de enviar'))
            if self.controller.gerando:
                return
            self._follow_output = True
            self.controller.gerar(self._prompt_text(), model)
        except (ValueError, RuntimeError) as exc:
            self._toast(str(exc))
            self.prompt.grab_focus()
            return
        self.prompt.get_buffer().set_text('')

    def _message_added(self, _controller, mensagem) -> None:
        self.pilha_conversa.set_visible_child_name('mensagens')
        user = mensagem.usuario
        balloon = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True)
        if user:
            balloon.add_css_class('message-user')
            balloon.set_margin_start(24)
        else:
            balloon.set_margin_end(24)
        author_row = Gtk.Box(spacing=8)
        author = Gtk.Label(label=_('Você') if user else _('Assistente'), xalign=0, hexpand=True)
        author.add_css_class('heading')
        author_row.append(author)
        if not user:
            copy = Gtk.Button(icon_name='edit-copy-symbolic',
                              tooltip_text=_('Copiar resposta'), valign=Gtk.Align.CENTER)
            copy.add_css_class('flat')
            copy.connect('clicked', lambda *_: self._copiar_texto(mensagem.texto))
            author_row.append(copy)
        balloon.append(author_row)
        label = Gtk.Label(label=mensagem.texto, xalign=0, selectable=True, hexpand=True)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_natural_wrap_mode(Gtk.NaturalWrapMode.NONE)
        label.add_css_class('document')
        balloon.append(label)
        self.caixa_mensagens.append(balloon)
        self._labels[id(mensagem)] = label
        self._schedule_scroll()

    def _message_updated(self, _controller, mensagem) -> None:
        label = self._labels.get(id(mensagem))
        if label is not None:
            label.set_text(mensagem.texto)
            self._schedule_scroll()

    def _limpar_baloes(self) -> None:
        self._labels.clear()
        child = self.caixa_mensagens.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.caixa_mensagens.remove(child)
            child = next_child

    def _confirmar_limpar(self, *_args) -> None:
        dialog = Adw.AlertDialog(
            heading=_('Limpar esta conversa?'),
            body=_('As mensagens desta conversa serão removidas. Esta ação não pode ser desfeita.'),
        )
        dialog.add_response('cancelar', _('Cancelar'))
        dialog.add_response('limpar', _('Limpar'))
        dialog.set_response_appearance('limpar', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancelar')
        dialog.set_close_response('cancelar')
        dialog.connect('response', lambda _d, response:
                       self.limpar_conversa() if response == 'limpar' and not self._closed else None)
        dialog.present(self)

    def limpar_conversa(self, *_args) -> None:
        if self.controller.gerando:
            self._toast(_('Interrompa a geração antes de limpar a conversa'))
            return
        if self.controller.conversa_atual:
            self.controller.conversa_atual.limpar()
            self._present_conversation()
            self._toast(_('Conversa limpa'))

    def _copiar_texto(self, text: str) -> None:
        if text:
            self.get_display().get_clipboard().set(text)
            self._toast(_('Resposta copiada'))

    def copiar_resposta(self, *_args) -> None:
        if self.controller.conversa_atual:
            self._copiar_texto(self.controller.conversa_atual.ultima_resposta)

    def _toast(self, text: str) -> None:
        if not self._closed:
            self.toast_overlay.add_toast(Adw.Toast(title=text, timeout=4, use_markup=False))

    def _download(self, *_args) -> None:
        DownloadDialog(self.controller, self._toast).present(self)

    def _about(self, *_args) -> None:
        Adw.AboutDialog(
            application_name=_('Instances'), application_icon=APP_ID, version=VERSION,
            comments=_('Converse com modelos locais usando o Ollama.'),
            translator_credits=_('translator-credits'),
        ).present(self)

    def _shortcuts(self, *_args) -> None:
        dialog = Adw.ShortcutsDialog()
        section = Adw.ShortcutsSection(title=_('Conversas'))
        for title, action in (
            (_('Nova conversa'), 'nova-conversa'),
            (_('Enviar mensagem'), 'enviar'),
            (_('Interromper resposta'), 'parar'),
            (_('Mostrar ou ocultar conversas'), 'alternar-sidebar'),
            (_('Buscar conversas'), 'buscar-conversas'),
            (_('Atalhos de teclado'), 'atalhos'),
        ):
            section.add(Adw.ShortcutsItem(title=title, action_name=f'win.{action}'))
        dialog.add(section)
        dialog.present(self)

    def _alternar_sidebar(self, *_args) -> None:
        self.divisao.set_show_sidebar(not self.divisao.get_show_sidebar())

    def _sidebar_changed(self, *_args) -> None:
        self.botao_mostrar_sidebar.set_active(self.divisao.get_show_sidebar())
        self.sidebar.set_collapsed(self.divisao.get_collapsed())

    def _buscar_conversas(self, *_args) -> None:
        self.divisao.set_show_sidebar(True)
        self.sidebar.buscar()

    def _recolher_sidebar(self) -> None:
        if self.divisao.get_collapsed():
            self.divisao.set_show_sidebar(False)

    def _usar_sugestao(self, text: str) -> None:
        self.prompt.get_buffer().set_text(text)
        self.prompt.grab_focus()

    def _scroll_changed(self, adjustment) -> None:
        if not self._scroll_pending:
            distance = adjustment.get_upper() - adjustment.get_page_size() - adjustment.get_value()
            self._follow_output = distance < 48

    def _schedule_scroll(self) -> None:
        if not self._scroll_pending and self._follow_output:
            self._scroll_pending = True
            # Espera o layout dos novos fragmentos antes de consultar o ajuste.
            GLib.timeout_add(40, self._rolar_para_fim)

    def _rolar_para_fim(self) -> bool:
        if not self._closed:
            adjustment = self.scroll_conversa.get_vadjustment()
            adjustment.set_value(max(0, adjustment.get_upper() - adjustment.get_page_size()))
        self._scroll_pending = False
        return False

    def _close(self, *_args) -> bool:
        self._closed = True
        self._stop_download_pulse()
        self.controller.fechar()
        for handler in self._handlers:
            self.controller.disconnect(handler)
        return False
