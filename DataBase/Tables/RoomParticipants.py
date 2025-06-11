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

#checked

def get_room_participant_count(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Room_Participants WHERE room_id = ?", (room_id,))
        row = cur.fetchone() 
        return row[0] if row else 0


def join_room(user_id, room_id):
    with connect() as conn:
        cur = conn.cursor()
        # Проверяем статус комнаты
        cur.execute("SELECT status FROM Room WHERE id = ?", (room_id,))
        room_status = cur.fetchone()

        if not room_status or room_status[0] != 'waiting':
            return False  # Комната не в состоянии 'waiting'

        # Проверяем, не находится ли пользователь уже в комнате
        cur.execute("SELECT 1 FROM Room_Participants WHERE user_id = ? AND room_id = ?", (user_id, room_id))
        if cur.fetchone():
            return False  # Пользователь уже в комнате

        cur.execute("INSERT INTO Room_Participants (user_id, room_id, score) VALUES (?, ?, 0)", (user_id, room_id))
        conn.commit()
        return True
        
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
    
def remove_participant_from_room(room_id, user_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Room_Participants
            WHERE room_id = ? AND user_id = ?
        """, (room_id, user_id))
        conn.commit()
