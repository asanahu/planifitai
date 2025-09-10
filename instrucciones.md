web-1     | INFO:     172.18.0.1:52046 - "POST /api/v1/routines/1/days/2/complete HTTP/1.1" 404 Not Found
web-1     | INFO:     172.18.0.1:52046 - "GET /api/v1/progress?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 307 Temporary Redirect
db-1      | 2025-09-10 20:50:27.858 UTC [1215] ERROR:  invalid input value for enum progressmetric: "workout" at character 442
db-1      | 2025-09-10 20:50:27.858 UTC [1215] STATEMENT:  SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
db-1      |     FROM progress_entries 
db-1      |     WHERE progress_entries.user_id = 1 AND progress_entries.metric = 'workout' AND progress_entries.date >= '2025-09-03'::date AND progress_entries.date <= '2025-09-10'::date ORDER BY progress_entries.date ASC
web-1     | Unexpected error: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     | INFO:     172.18.0.1:52046 - "GET /api/v1/progress/?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 500 Internal Server Error
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | 
web-1     | ERROR:    Exception in ASGI application
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
web-1     |     result = await app(  # type: ignore[func-returns-value]
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
web-1     |     return await self.app(scope, receive, send)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/applications.py", line 1054, in __call__
web-1     |     await super().__call__(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/applications.py", line 113, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 186, in __call__
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | INFO:     172.18.0.1:52058 - "GET /api/v1/progress?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 307 Temporary Redirect
db-1      | 2025-09-10 20:50:28.908 UTC [1232] ERROR:  invalid input value for enum progressmetric: "workout" at character 442
db-1      | 2025-09-10 20:50:28.908 UTC [1232] STATEMENT:  SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
db-1      |     FROM progress_entries 
db-1      |     WHERE progress_entries.user_id = 1 AND progress_entries.metric = 'workout' AND progress_entries.date >= '2025-09-03'::date AND progress_entries.date <= '2025-09-10'::date ORDER BY progress_entries.date ASC
web-1     | Unexpected error: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     | INFO:     172.18.0.1:52058 - "GET /api/v1/progress/?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 500 Internal Server Error
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | 
web-1     | ERROR:    Exception in ASGI application
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
web-1     |     result = await app(  # type: ignore[func-returns-value]
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
web-1     |     return await self.app(scope, receive, send)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/applications.py", line 1054, in __call__
web-1     |     await super().__call__(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/applications.py", line 113, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 186, in __call__
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | INFO:     172.18.0.1:34992 - "GET /api/v1/progress?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 307 Temporary Redirect
db-1      | 2025-09-10 20:50:30.958 UTC [1219] ERROR:  invalid input value for enum progressmetric: "workout" at character 442
db-1      | 2025-09-10 20:50:30.958 UTC [1219] STATEMENT:  SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
db-1      |     FROM progress_entries 
db-1      |     WHERE progress_entries.user_id = 1 AND progress_entries.metric = 'workout' AND progress_entries.date >= '2025-09-03'::date AND progress_entries.date <= '2025-09-10'::date ORDER BY progress_entries.date ASC
web-1     | Unexpected error: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     | INFO:     172.18.0.1:34992 - "GET /api/v1/progress/?metric=workout&start=2025-09-03&end=2025-09-10 HTTP/1.1" 500 Internal Server Error
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)
web-1     | 
web-1     | ERROR:    Exception in ASGI application
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | psycopg2.errors.InvalidTextRepresentation: invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | 
web-1     | The above exception was the direct cause of the following exception:
web-1     | 
web-1     | Traceback (most recent call last):
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
web-1     |     result = await app(  # type: ignore[func-returns-value]
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
web-1     |     return await self.app(scope, receive, send)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/applications.py", line 1054, in __call__
web-1     |     await super().__call__(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/applications.py", line 113, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 186, in __call__
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
web-1     |     await self.app(scope, receive, _send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 93, in __call__
web-1     |     await self.simple_response(scope, receive, send, request_headers=headers)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 144, in simple_response
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
web-1     |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 716, in __call__
web-1     |     await self.middleware_stack(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 736, in app
web-1     |     await route.handle(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 290, in handle
web-1     |     await self.app(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 78, in app
web-1     |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
web-1     |     raise exc
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
web-1     |     await app(scope, receive, sender)
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 75, in app
web-1     |     response = await f(request)
web-1     |                ^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 302, in app
web-1     |     raw_response = await run_endpoint_function(
web-1     |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 215, in run_endpoint_function
web-1     |     return await run_in_threadpool(dependant.call, **values)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
web-1     |     return await anyio.to_thread.run_sync(func)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/to_thread.py", line 56, in run_sync
web-1     |     return await get_async_backend().run_sync_in_worker_thread(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 2476, in run_sync_in_worker_thread
web-1     |     return await future
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 967, in run
web-1     |     result = context.run(func, *args)
web-1     |              ^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/routers.py", line 41, in list_progress
web-1     |     return services.list_entries(db, current_user.id, metric, start, end)
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/code/app/progress/services.py", line 56, in list_entries
web-1     |     return query.order_by(models.ProgressEntry.date.asc()).all()
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2704, in all
web-1     |     return self._iter().all()  # type: ignore
web-1     |            ^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
web-1     |     result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
web-1     |                                                   ^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
web-1     |     return self._execute_internal(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
web-1     |     result: Result[Any] = compile_state_cls.orm_execute_statement(
web-1     |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
web-1     |     result = conn.execute(
web-1     |              ^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
web-1     |     return meth(
web-1     |            ^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
web-1     |     return connection._execute_clauseelement(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
web-1     |     ret = self._execute_context(
web-1     |           ^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
web-1     |     return self._exec_single_context(
web-1     |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
web-1     |     self._handle_dbapi_exception(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
web-1     |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
web-1     |     self.dialect.do_execute(
web-1     |   File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
web-1     |     cursor.execute(statement, parameters)
web-1     | sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum progressmetric: "workout"
web-1     | LINE 3: ...entries.user_id = 1 AND progress_entries.metric = 'workout' ...
web-1     |                                                              ^
web-1     | 
web-1     | [SQL: SELECT progress_entries.id AS progress_entries_id, progress_entries.user_id AS progress_entries_user_id, progress_entries.date AS progress_entries_date, progress_entries.metric AS progress_entries_metric, progress_entries.value AS progress_entries_value, progress_entries.unit AS progress_entries_unit, progress_entries.notes AS progress_entries_notes 
web-1     | FROM progress_entries 
web-1     | WHERE progress_entries.user_id = %(user_id_1)s AND progress_entries.metric = %(metric_1)s AND progress_entries.date >= %(date_1)s AND progress_entries.date <= %(date_2)s ORDER BY progress_entries.date ASC]
web-1     | [parameters: {'user_id_1': 1, 'metric_1': 'workout', 'date_1': datetime.date(2025, 9, 3), 'date_2': datetime.date(2025, 9, 10)}]
web-1     | (Background on this error at: https://sqlalche.me/e/20/9h9h)