import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Room_Participants

PK  id      int
---------------
FK1 user_id int
---------------
FK2 room_id int
---------------
    score   int

"""

def join_room(user_id, room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Room_Participants (user_id, room_id, score) VALUES (?, ?, 0)",
                    (user_id, room_id))
        
def update_player_score(user_id, room_id, score):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Room_Participants SET score = score + ? WHERE user_id = ? AND room_id = ?",
                    (score, user_id, room_id))
        
def get_room_participants(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT U.name, RP.score FROM Room_Participants RP
            JOIN User U ON RP.user_id = U.id
            WHERE RP.room_id = ? ORDER BY RP.score DESC""",
            (room_id,))
        return cur.fetchall()