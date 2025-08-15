from contextlib import contextmanager
from sqlalchemy import event
from sqlalchemy.engine import Engine

@contextmanager
def count_queries(engine: Engine):
    count = {"n": 0, "stmts": []}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        count["n"] += 1
        count["stmts"].append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield count
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
