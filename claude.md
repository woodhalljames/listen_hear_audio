listen_hear_audio_local_django
f742530d273a
listen_hear_audio_local_django:latest
8000:8000
STATUS
Exited (1) (11 seconds ago)


wait-for-it: waiting 30 seconds for postgres:5432

wait-for-it: postgres:5432 is available after 0 seconds

PostgreSQL is available

Traceback (most recent call last):

  File "/app/manage.py", line 30, in <module>

    main()

    ~~~~^^

  File "/app/manage.py", line 26, in main

    execute_from_command_line(sys.argv)

    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line

    utility.execute()

    ~~~~~~~~~~~~~~~^^

  File "/app/.venv/lib/python3.13/site-packages/django/core/management/__init__.py", line 416, in execute

    django.setup()

    ~~~~~~~~~~~~^^

  File "/app/.venv/lib/python3.13/site-packages/django/__init__.py", line 24, in setup

    apps.populate(settings.INSTALLED_APPS)

    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/django/apps/registry.py", line 124, in populate

    app_config.ready()

    ~~~~~~~~~~~~~~~~^^

  File "/app/.venv/lib/python3.13/site-packages/django/contrib/admin/apps.py", line 27, in ready

    self.module.autodiscover()

    ~~~~~~~~~~~~~~~~~~~~~~~~^^

  File "/app/.venv/lib/python3.13/site-packages/django/contrib/admin/__init__.py", line 52, in autodiscover

    autodiscover_modules("admin", register_to=site)

    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/django/utils/module_loading.py", line 58, in autodiscover_modules

    import_module("%s.%s" % (app_config.name, module_to_search))

    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.13/importlib/__init__.py", line 88, in import_module