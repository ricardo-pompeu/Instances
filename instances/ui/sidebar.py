"""Navegação com os componentes nativos Adw.Sidebar e Adw.SidebarItem."""

from ..resources import action_icon, template
from gi.repository import Adw, GObject, Gtk


@template('sidebar')
class ConversationSidebar(Gtk.Box):
    """Relaciona itens da sidebar a conversas, sem administrar a sessão."""

    __gtype_name__ = 'InstancesSidebar'
    __gsignals__ = {
        'selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    new_button = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    navigation = Gtk.Template.Child()
    section = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.new_button.set_child(Gtk.Image(
            gicon=action_icon('plus-framed-symbolic'), pixel_size=16))
        self._conversations = {}
        self._selected_conversation = None
        self.search_bar.connect_entry(self.search_entry)
        self.navigation.connect('activated', self._activated)

    def adicionar_conversa(self, conversa) -> None:
        # Uma busca antiga não deve ocultar a conversa recém-criada.
        self.search_entry.set_text('')
        item = Adw.SidebarItem(title=conversa.titulo,
                               icon_name='chat-message-new-symbolic')
        self._conversations[item] = conversa
        self.section.prepend(item)
        self.navigation.set_selected(0)
        self._selected_conversation = conversa

    def atualizar_titulos(self) -> None:
        for item, conversa in self._conversations.items():
            if item.get_title() != conversa.titulo:
                item.set_title(conversa.titulo)
            item.set_tooltip(conversa.titulo)

    def set_busy(self, busy: bool) -> None:
        for item in self._conversations:
            item.set_enabled(not busy)

    def set_collapsed(self, collapsed: bool) -> None:
        self.navigation.set_mode(
            Adw.SidebarMode.PAGE if collapsed else Adw.SidebarMode.SIDEBAR
        )

    def buscar(self) -> None:
        self.search_button.set_active(True)
        self.search_entry.grab_focus()

    def _activated(self, _sidebar, _index) -> None:
        item = self.navigation.get_selected_item()
        if item in self._conversations:
            conversa = self._conversations[item]
            self._selected_conversation = conversa
            self.emit('selected', conversa)
