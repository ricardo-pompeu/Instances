test_environment = environment()
test_environment.set('PYTHONPATH', meson.project_source_root())
test(
  'core-and-controller', python,
  args: ['-m', 'unittest', 'discover', '-s', meson.current_source_dir(), '-v'],
  env: test_environment,
)
ui_environment = environment()
ui_environment.set('PYTHONPATH', meson.project_source_root())
ui_environment.set(
  'INSTANCES_RESOURCE_FILE', meson.project_build_root() / 'data' / 'instances.gresource',
)
ui_environment.set('GSK_RENDERER', 'cairo')
ui_environment.set('G_DEBUG', 'fatal-criticals')
test(
  'ui-smoke', python,
  args: files('../tools/ui_smoke.py'), env: ui_environment, timeout: 30,
)
