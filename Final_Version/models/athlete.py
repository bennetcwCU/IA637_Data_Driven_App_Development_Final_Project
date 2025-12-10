from baseObject import baseObject
class Athlete(baseObject):
    def __init__(self): super().setup()

    def delete_by_id(self, athlete_id):
        sql = "DELETE FROM Athlete WHERE AthleteID = %s"
        self.cur.execute(sql, (athlete_id,))
        self.conn.commit()