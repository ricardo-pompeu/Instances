project('instances', version: '0.1', meson_version: '>= 1.0.0')

python = import('python').find_installation('python3', modules: ['gi', 'requests'])
gnome = import('gnome')
i18n = import('i18n')

resource_compiler = find_program('glib-compile-resources', required: false)
if not resource_compiler.found()
  error(
    'Falta glib-compile-resources. No Fedora, instale glib2-devel: ' +
    'sudo dnf install glib2-devel. Depois execute meson setup --reconfigure novamente.'
  )
endif

runtime_check = run_command(python, files('tools/check_runtime.py'), check: true)
message(runtime_check.stdout().strip())

app_id = 'com.example.Instances'
pkgdatadir = get_option('prefix') / get_option('datadir') / 'instances'
localedir = get_option('prefix') / get_option('localedir')
configuration = configuration_data()
configuration.set('APP_ID', app_id)
configuration.set('VERSION', meson.project_version())
configuration.set('DATA_DIR', pkgdatadir)
configuration.set('LOCALE_DIR', localedir)
configuration.set('PYTHON', python.full_path())

subdir('instances')
subdir('data')
subdir('po')
subdir('tests')

gnome.post_install(gtk_update_icon_cache: true)

development = environment()
development.prepend('PATH', meson.current_build_dir() / 'data')
development.prepend('PYTHONPATH', meson.current_source_dir())
development.set('INSTANCES_RESOURCE_FILE', meson.current_build_dir() / 'data' / 'instances.gresource')
meson.add_devenv(development)
