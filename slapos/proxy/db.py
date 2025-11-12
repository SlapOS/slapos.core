from flask import g, current_app
from slapos.proxy.db_version import DB_VERSION


def execute_db(table, query, args=(), one=False, db_version=DB_VERSION, db=None):
  if not db:
    db = g.db
  query = query % (table + db_version,)
  current_app.logger.debug(query)
  try:
    cur = db.execute(query, args)
  except Exception:
    current_app.logger.error(
      'There was some issue during processing query %r on table %r with args %r',
      query, table, args)
    raise
  rv = ({cur.description[idx][0]: value
    for idx, value in enumerate(row)} for row in cur)
  return next(rv, None) if one else list(rv)