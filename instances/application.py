"""Ciclo de vida da aplicação GTK."""

from gettext import gettext as _
import logging
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, GLib, Gtk

from .config import APP_ID
from .resources import initialize


class InstancesApplication(Adw.Application):
    """Inicializa recursos antes da criação de qualquer janela."""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_startup(self):
        Adw.Application.do_startup(self)
        initialize()
        GLib.set_application_name(_('Instances'))
        Gtk.Window.set_default_icon_name(APP_ID)
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self._quit)
        self.add_action(action)
        self.set_accels_for_action('app.quit', ['<Control>q'])
        self.set_accels_for_action('window.close', ['<Control>w'])

    def _quit(self, *_args):
        for window in self.get_windows():
            window.close()
        self.quit()

    def do_activate(self):
        from .ui.window import InstancesWindow

        janela = self.get_active_window()
        if janela is None:
            janela = InstancesWindow(self)
        janela.present()


def main(argv: list[str] | None = None) -> int:
    """Entrada comum ao módulo Python e ao launcher instalado."""
    logging.basicConfig(level=logging.WARNING)
    return InstancesApplication().run(sys.argv if argv is None else argv)
