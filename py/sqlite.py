import sqlite3 as s

class s3db:
    def __init__(self):
        self.conn=None

    def open(self,dbpath):
        if self.conn is not None:
            return True
        try:
            self.conn=s.connect(dbpath)

        except Exception as e:
            return False