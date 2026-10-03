"""Valida o runtime GI utilizado pelo interpretador escolhido pelo Meson."""

import sys

import gi
import requests

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk

checks = (
    ('Python', sys.version_info[:3], (3, 10, 0)),
    ('GTK', (Gtk.get_major_version(), Gtk.get_minor_version(),
             Gtk.get_micro_version()), (4, 22, 0)),
    ('Libadwaita', (Adw.get_major_version(), Adw.get_minor_version(),
                   Adw.get_micro_version()), (1, 9, 0)),
)
for name, actual, minimum in checks:
    if actual < minimum:
        raise SystemExit(f'{name}: requer {minimum}; encontrado {actual}')
    print(f'{name}: {actual}')
requests_version = tuple(int(part) for part in requests.__version__.split('.')[:2])
if not (2, 28) <= requests_version < (3, 0):
    raise SystemExit('Requests deve ser >= 2.28 e < 3')
