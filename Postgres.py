import psycopg2
import logging

from typing import Union


logger = logging.getLogger('gunicorn.error')


class Postgres:
    conn = None

    def __init__(self, dsn: Union[str, None]=None) -> None:
        self.conn = psycopg2.connect(dsn)

    def fetchall(self, sql: str) -> Union[tuple, bool]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            logger.error(e)

        return False


    def execute(self, sql: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            logger.error(e)

            return False


        return True
