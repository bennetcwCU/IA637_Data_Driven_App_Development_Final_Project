# models/user.py
import bcrypt
from baseObject import baseObject

class User(baseObject):
    def __init__(self):
        super().setup()

    def tryLogin(self, email, pwd):
        self.getByField('email', email)
        if not self.data:
            return False
        return bcrypt.checkpw(pwd.encode(), self.data[0]['hashPassword'].encode())

    # ADD THIS METHOD
    def update(self, n=0):
        """Update a single record in the database"""
        if not self.data or n >= len(self.data):
            return False
        
        keys = [k for k in self.data[n] if k in self.fields and k != self.pk]
        if not keys:
            return False
        
        setters = ', '.join(f'`{k}`=%s' for k in keys)
        sql = f"UPDATE `{self.tn}` SET {setters} WHERE `{self.pk}`=%s"
        values = [self.data[n][k] for k in keys]
        values.append(self.data[n][self.pk])
        
        try:
            self.cur.execute(sql, values)
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False