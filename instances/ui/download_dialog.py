"""Entrada do nome de um modelo a baixar."""

from gettext import gettext as _

from ..resources import template
from gi.repository import Adw, Gtk


@template('download-dialog')
class DownloadDialog(Adw.AlertDialog):
    __gtype_name__ = 'InstancesDownloadDialog'
    entry = Gtk.Template.Child()

    def __init__(self, controller, notice):
        super().__init__()
        self._controller = controller
        self._notice = notice
        self.add_response('cancelar', _('Cancelar'))
        self.add_response('baixar', _('Baixar'))
        self.set_response_appearance('baixar', Adw.ResponseAppearance.SUGGESTED)
        self.set_default_response('baixar')
        self.set_close_response('cancelar')
        self.set_response_enabled('baixar', False)
        self.entry.connect('changed', self._changed)
        self.connect('response', self._response)

    def _changed(self, entry) -> None:
        text = entry.get_text().strip()
        valid = bool(text) and not any(c.isspace() for c in text)
        self.set_response_enabled('baixar', valid)

    def _response(self, _dialog, response) -> None:
        if response == 'baixar':
            try:
                self._controller.baixar(self.entry.get_text())
            except (ValueError, RuntimeError) as exc:
                self._notice(str(exc))
