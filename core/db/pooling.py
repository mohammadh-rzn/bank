# core/db/pooling.py
from django.db.backends.postgresql.base import DatabaseWrapper as PGDatabaseWrapper
from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper

class PooledDatabaseWrapper(PGDatabaseWrapper):  # or MySQLDatabaseWrapper
    def get_new_connection(self, conn_params):
        conn = super().get_new_connection(conn_params)
        # Configure connection timeout and other settings
        conn.set_session(autocommit=True)
        return conn

    def close(self):
        # Override close to return connection to pool instead of closing
        if self.connection is not None:
            with self.wrap_database_errors:
                return self.connection_pool.putconn(self.connection)
        self.connection = None