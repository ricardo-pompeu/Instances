configure_file(
  input: 'config.py.in', output: '_build_config.py',
  configuration: configuration,
  install_dir: pkgdatadir / 'instances',
)
install_data(
  '__init__.py', '__main__.py', 'application.py', 'config.py',
  'controller.py', 'conversations.py', 'ollama.py', 'service.py', 'resources.py',
  install_dir: pkgdatadir / 'instances',
)
install_data(
  'ui/__init__.py', 'ui/window.py', 'ui/sidebar.py', 'ui/download_dialog.py',
  install_dir: pkgdatadir / 'instances' / 'ui',
)
