gnome.compile_resources(
  'instances', 'instances.gresource.xml',
  source_dir: meson.current_source_dir(),
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)
launcher = configure_file(
  input: 'instances.in', output: 'instances', configuration: configuration,
  install_dir: get_option('bindir'), install_mode: 'rwxr-xr-x',
)
# install_mode aplica-se à instalação; o launcher do build também é executável.
run_command(
  python, '-c', 'import os, sys; os.chmod(sys.argv[1], 0o755)', launcher,
  check: true,
)
i18n.merge_file(
  input: app_id + '.desktop.in', output: app_id + '.desktop',
  type: 'desktop', po_dir: '../po',
  install: true, install_dir: get_option('datadir') / 'applications',
)
install_data(
  'icons/hicolor/scalable/apps/' + app_id + '.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
)

install_data(
  'icons/hicolor/symbolic/apps/' + app_id + '-symbolic.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/symbolic/apps',
)

install_data(
  'icons/hicolor/symbolic/actions/paper-plane-symbolic.svg',
  'icons/hicolor/symbolic/actions/plus-framed-symbolic.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/symbolic/actions',
)
