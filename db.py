import os
import psycopg2


class Database(object):
    """ """

    def __init__(self, dbconn=None):
        if dbconn is None:
            default_dbconn = "dbname='ckan' user='ckan' host='127.0.0.1' port='35433' password='ckan'"
            dbconn = os.getenv("CKAN_DB_URI", default_dbconn)
        self.conn = psycopg2.connect(dbconn)
        self.cursor = self.conn.cursor()

    def get_cursor(self):
        return self.cursor

    def close(self):
        self.conn.close()

    def resource_grade_update(self, id, grade):
        q = f"""
        UPDATE resource SET grade = '{grade}'
        WHERE id = '{id}'
        """
        try:
            self.cursor.execute(q)
            self.conn.commit()
        except Exception as e:
            print(e, end="\r")
            self.conn.rollback()
