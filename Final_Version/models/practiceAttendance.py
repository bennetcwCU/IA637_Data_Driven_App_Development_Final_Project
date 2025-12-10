from baseObject import baseObject
class PracticeAttendance(baseObject):
    def __init__(self): super().setup()

    def delete_by_athlete(self, athlete_id):
        sql = f"DELETE FROM `{self.tn}` WHERE AthleteID = %s"
        self.cur.execute(sql, (athlete_id,))
        self.conn.commit()