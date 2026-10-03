"""Carrega templates e estilos no código-fonte, build ou instalação."""

import gettext
import locale
import os
from pathlib import Path

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, Gtk

from .config import DATA_DIR, GETTEXT_DOMAIN, LOCALE_DIR, RESOURCE_PREFIX

_resource = None
_initialized = False


def initialize() -> None:
    """Registra os recursos antes da importação das classes Gtk.Template."""
    global _resource, _initialized
    if _initialized:
        return
    locale.bindtextdomain(GETTEXT_DOMAIN, LOCALE_DIR)
    gettext.bindtextdomain(GETTEXT_DOMAIN, LOCALE_DIR)
    gettext.textdomain(GETTEXT_DOMAIN)
    resource_file = Path(os.environ.get(
        'INSTANCES_RESOURCE_FILE', str(Path(DATA_DIR) / 'instances.gresource')
    ))
    if resource_file.is_file():
        _resource = Gio.Resource.load(str(resource_file))
        Gio.resources_register(_resource)
    _initialized = True


def template(name: str):
    """Usa GResource no build/instalação e XML local na execução direta."""
    initialize()
    if _resource is not None:
        return Gtk.Template(resource_path=f'{RESOURCE_PREFIX}/ui/{name}.ui')
    return Gtk.Template(filename=str(Path(DATA_DIR) / 'ui' / f'{name}.ui'))


def action_icon(name: str):
    """Carrega um SVG simbólico próprio sem depender do cache do tema."""
    initialize()
    if _resource is not None:
        file = Gio.File.new_for_uri(
            f'resource://{RESOURCE_PREFIX}/icons/symbolic/actions/{name}.svg'
        )
    else:
        file = Gio.File.new_for_path(str(
            Path(DATA_DIR) / 'icons' / 'hicolor' / 'symbolic' / 'actions' / f'{name}.svg'
        ))
    return Gio.FileIcon.new(file)


def load_styles(display) -> None:
    icon_theme = Gtk.IconTheme.get_for_display(display)
    if _resource is not None:
        icon_theme.add_resource_path(f'{RESOURCE_PREFIX}/icons')
    else:
        icon_theme.add_search_path(str(Path(DATA_DIR) / 'icons'))
    provider = Gtk.CssProvider()
    if _resource is not None:
        provider.load_from_resource(f'{RESOURCE_PREFIX}/style.css')
    else:
        provider.load_from_path(str(Path(DATA_DIR) / 'style.css'))
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
