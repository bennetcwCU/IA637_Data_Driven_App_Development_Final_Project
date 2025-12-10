import yaml
from pathlib import Path
import pymysql

class baseObject:
    def setup(self, config_path='config.yml'):
        self.data = []
        self.pk = None
        config = yaml.safe_load(Path(config_path).read_text())
        self.tn = config['tables'][type(self).__name__.lower()]

        self.conn = pymysql.connect(
            host=config['db']['host'],
            port=3306,
            user=config['db']['user'],
            passwd=config['db']['pw'],
            db=config['db']['db'],
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cur = self.conn.cursor()
        self.getFields()

    def set(self, d): self.data = [d]

    def getFields(self):
        self.fields = []
        self.cur.execute(f"DESCRIBE `{self.tn}`")
        for row in self.cur:
            if row['Extra'] and 'auto_increment' in row['Extra']:
                self.pk = row['Field']
            else:
                self.fields.append(row['Field'])

    def insert(self, n=0):
        keys = [k for k in self.data[n] if k in self.fields]
        cols = ', '.join(f'`{k}`' for k in keys)
        ph = ', '.join(['%s'] * len(keys))
        sql = f"INSERT INTO `{self.tn}` ({cols}) VALUES ({ph})"
        vals = [self.data[n][k] for k in keys]
        self.cur.execute(sql, vals)
        if self.pk:
            self.data[n][self.pk] = self.cur.lastrowid

    def getAll(self, order=''):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}`"
        if order: sql += f" ORDER BY {order}"
        self.cur.execute(sql)
        self.data = self.cur.fetchall()

    def getById(self, id_val):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}` WHERE `{self.pk}`=%s"
        self.cur.execute(sql, (id_val,))
        self.data = self.cur.fetchall()

    def getByField(self, field, value):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}` WHERE `{field}`=%s"
        self.cur.execute(sql, (value,))
        self.data = self.data = self.cur.fetchall()

    def delete(self, id_val):
        if not self.pk:
            return False
        sql = f"DELETE FROM `{self.tn}` WHERE `{self.pk}` = %s"
        self.cur.execute(sql, (id_val,))
        self.conn.commit()   # ← This commits the delete
        return True    