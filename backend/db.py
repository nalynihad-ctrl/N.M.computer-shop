"""Database layer.

Tries to connect to MySQL first. If MySQL is unavailable (not installed, not
running, wrong credentials or PyMySQL missing) it transparently falls back to a
local SQLite file so the shop still works. Both backends share the same SQL,
written with ``?`` placeholders which are translated to ``%s`` for MySQL.

Stage 3 - injection prevention
------------------------------
* Every *value* reaches the database through a ``?`` placeholder, so user data
  is always bound by the driver and never parsed as SQL.
* SQL *identifiers* (table and column names) cannot be bound as parameters, so
  the few places that must interpolate one go through :meth:`Database.identifier`
  first, which only accepts a plain ``[A-Za-z_][A-Za-z0-9_]*`` name. That
  closes the classic "parameterise everything except the table name" hole.
"""

import os
import re
import sqlite3
import threading

try:
    import pymysql
    import pymysql.cursors

    HAVE_PYMYSQL = True
except Exception:  # pragma: no cover - depends on environment
    HAVE_PYMYSQL = False


# A SQL identifier is a bare word. Anything containing quotes, semicolons,
# spaces, comment markers or backticks can never be a legitimate table/column
# name here, so rejecting them is safe and non-breaking.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
# A column definition is a short type clause such as "TEXT" or
# "VARCHAR(255) NOT NULL". Only these trailing keywords are permitted, so an
# arbitrary word such as "a b" is rejected instead of being treated as a
# modifier.
_DEFINITION_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*"
    r"(?:\s*\(\s*\d{1,5}\s*\))?"
    r"(?:\s+(?:NOT|NULL|UNIQUE|PRIMARY|KEY|AUTO_INCREMENT))*"
    r"(?:\s+DEFAULT\s+[A-Za-z0-9_.]{1,32})?$"
)


class UnsafeIdentifierError(ValueError):
    """Raised when a string that must be a bare SQL identifier is not one."""


def safe_identifier(name, what="identifier"):
    """Return ``name`` if it is a plain SQL identifier, else raise.

    This is a hard allowlist, not a denylist: it does not try to strip quotes
    or escape metacharacters, because a value that needs escaping is a value
    that should never have been interpolated in the first place.
    """
    if not isinstance(name, str) or not _IDENTIFIER_RE.match(name):
        raise UnsafeIdentifierError(
            "Refusing to interpolate %r as a SQL %s: only plain "
            "[A-Za-z_][A-Za-z0-9_]* names are allowed." % (name, what)
        )
    return name


def safe_definition(definition):
    """Return a column definition if it is a simple type clause, else raise."""
    if not isinstance(definition, str) or not _DEFINITION_RE.match(definition.strip()):
        raise UnsafeIdentifierError(
            "Refusing to interpolate %r as a SQL column definition." % (definition,)
        )
    return definition.strip()


class Database:
    # Exposed so callers can validate a name before building a statement.
    identifier = staticmethod(safe_identifier)

    def __init__(self, mysql_config, mysql_database, sqlite_path):
        self.mysql_config = dict(mysql_config)
        self.mysql_database = mysql_database
        self.sqlite_path = sqlite_path
        self.dialect = None
        self.backend_name = None
        self._lock = threading.Lock()
        self._connect()

    # -- connection ---------------------------------------------------------
    def _connect(self):
        if HAVE_PYMYSQL:
            try:
                # The database name comes from configuration, not from a
                # request, but it is still interpolated into DDL, so it must
                # be a plain identifier.
                safe_identifier(self.mysql_database, "database name")
                server = pymysql.connect(**self.mysql_config, autocommit=True)
                with server.cursor() as cur:
                    cur.execute(
                        "CREATE DATABASE IF NOT EXISTS `%s` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        % self.mysql_database
                    )
                    cur.execute("USE `%s`" % self.mysql_database)
                server.close()
                self.dialect = "mysql"
                self.backend_name = "MySQL (%s)" % self.mysql_database
                return
            except Exception as exc:  # fall through to sqlite
                print("[db] MySQL unavailable (%s); using SQLite fallback." % exc)
        else:
            print("[db] PyMySQL not installed; using SQLite fallback.")

        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        self.dialect = "sqlite"
        self.backend_name = "SQLite (%s)" % self.sqlite_path

    def _raw(self):
        if self.dialect == "mysql":
            return pymysql.connect(
                **self.mysql_config,
                database=self.mysql_database,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        conn = sqlite3.connect(self.sqlite_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _sql(self, sql):
        if self.dialect == "mysql":
            return sql.replace("?", "%s")
        return sql

    # -- helpers ------------------------------------------------------------
    def query(self, sql, params=()):
        """Execute a SELECT.

        ``sql`` is trusted application code; ``params`` is untrusted input and
        must always be passed bound. This is the only path user data can take
        into the database.
        """
        conn = self._raw()
        try:
            with self._lock:
                cur = conn.cursor()
                cur.execute(self._sql(sql), params)
                rows = cur.fetchall()
                cur.close()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def query_one(self, sql, params=()):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=()):
        conn = self._raw()
        try:
            with self._lock:
                cur = conn.cursor()
                cur.execute(self._sql(sql), params)
                lastrow = cur.lastrowid
                cur.close()
                conn.commit()
            return lastrow
        finally:
            conn.close()

    def execute_many(self, sql, seq):
        conn = self._raw()
        try:
            with self._lock:
                cur = conn.cursor()
                cur.executemany(self._sql(sql), seq)
                cur.close()
                conn.commit()
        finally:
            conn.close()

    # -- schema -------------------------------------------------------------
    def init_schema(self):
        pk = (
            "INTEGER PRIMARY KEY AUTO_INCREMENT"
            if self.dialect == "mysql"
            else "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

        statements = [
            f"""
            CREATE TABLE IF NOT EXISTS products (
                id {pk},
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                old_price REAL DEFAULT 0,
                discount INTEGER DEFAULT 0,
                image TEXT NOT NULL,
                images TEXT DEFAULT '[]',
                stock INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                specs TEXT DEFAULT '{{}}',
                created_at TEXT
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {pk},
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                api_token TEXT,
                token_expires_at TEXT,
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                city TEXT DEFAULT '',
                country TEXT DEFAULT '',
                created_at TEXT
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS orders (
                id {pk},
                user_id INTEGER,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                country TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                subtotal REAL NOT NULL,
                shipping REAL NOT NULL,
                discount REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'Pending',
                created_at TEXT
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS order_items (
                id {pk},
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                image TEXT
            )
            """,
        ]
        for stmt in statements:
            self.execute(stmt)

        # Migrations for databases created before these columns existed.
        self.add_column_if_missing("users", "token_expires_at", "TEXT")

    def columns(self, table):
        """Return the column names of ``table`` for the active backend."""
        table = safe_identifier(table, "table name")
        if self.dialect == "mysql":
            rows = self.query("SHOW COLUMNS FROM `%s`" % table)
            return [r["Field"] for r in rows]
        rows = self.query("PRAGMA table_info(%s)" % table)
        return [r["name"] for r in rows]

    def add_column_if_missing(self, table, column, definition):
        """Idempotently add a column, leaving existing rows and data intact."""
        # All three fragments are interpolated, so all three are allowlisted.
        table = safe_identifier(table, "table name")
        column = safe_identifier(column, "column name")
        definition = safe_definition(definition)
        if column in self.columns(table):
            return False
        self.execute(
            "ALTER TABLE `%s` ADD COLUMN `%s` %s" % (table, column, definition)
            if self.dialect == "mysql"
            else "ALTER TABLE %s ADD COLUMN %s %s" % (table, column, definition)
        )
        print("[db] added missing column %s.%s" % (table, column))
        return True

    def count(self, table):
        table = safe_identifier(table, "table name")
        row = self.query_one("SELECT COUNT(*) AS c FROM %s" % table)
        return int(row["c"]) if row else 0
