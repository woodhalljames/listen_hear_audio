 * Debugger PIN: 506-330-831

172.18.0.1 - - [02/Dec/2025 17:46:12] "GET /quote/checkout/ HTTP/1.1" 500 -

Traceback (most recent call last):

  File "/app/.venv/lib/python3.13/site-packages/django/db/backends/utils.py", line 105, in _execute

    return self.cursor.execute(sql, params)

           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/psycopg/cursor.py", line 97, in execute

    raise ex.with_traceback(None)

psycopg.errors.UndefinedColumn: column users_user.street does not exist

LINE 1: ..._user"."is_builder", "users_user"."company_name", "users_use...

                                                             ^


The above exception was the direct cause of the following exception:


Traceback (most recent call last):

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/wsgi.py", line 124, in __call__

    response = self.get_response(request)

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/base.py", line 140, in get_response

    response = self._middleware_chain(request)

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/exception.py", line 57, in inner

    response = response_for_exception(request, exc)

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/exception.py", line 141, in response_for_exception

    response = handle_uncaught_exception(

    

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/exception.py", line 182, in handle_uncaught_exception

    return debug.technical_500_response(request, *exc_info)

           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/django_extensions/management/technical_response.py", line 41, in null_technical_500_response

    raise exc_value.with_traceback(tb)

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/exception.py", line 55, in inner

    response = get_response(request)

  File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/base.py", line 197, in _get_response

    response = wrapped_callback(request, *callback_args, **callback_kwargs)

  File "/usr/local/lib/python3.13/contextlib.py", line 85, in inner

    return func(*args, **kwds)
  raise dj_exc_value.with_traceback(traceback) from exc_value

  File "/app/.venv/lib/python3.13/site-packages/django/db/backends/utils.py", line 105, in _execute

    return self.cursor.execute(sql, params)

           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^

  File "/app/.venv/lib/python3.13/site-packages/psycopg/cursor.py", line 97, in execute

    raise ex.with_traceback(None)

django.db.utils.ProgrammingError: column users_user.street does not exist

LINE 1: ..._user"."is_builder", "users_user"."company_name", "users_use...

                                                             ^

172.18.0.1 - - [02/Dec/2025 17:46:17] "GET /?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 200 -