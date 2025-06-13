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
        cur.execute("SELECT status FROM Room WHERE id = ?", (room_id,))
        room_status = cur.fetchone()

        if not room_status or room_status[0] != 'waiting':
            return False  # Комната не в состоянии 'waiting'

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
        conn.commit()
        
def get_room_participants(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT U.name FROM Room_Participants RP
            JOIN User U ON RP.user_id = U.user_tg_id
            WHERE RP.room_id = ? ORDER BY RP.score DESC""",
            (room_id,))
        return [row[0] for row in cur.fetchall()]
    
def get_room_participants_with_score(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT U.name, RP.score FROM Room_Participants RP
            JOIN User U ON RP.user_id = U.user_tg_id
            WHERE RP.room_id = ? ORDER BY RP.score DESC""",
            (room_id,))
        return cur.fetchall()
    
def get_room_participants_without_news(room_id,new_user_id):
     with connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT U.name FROM Room_Participants RP
                JOIN User U ON RP.user_id = U.user_tg_id
                WHERE RP.room_id = ? AND RP.user_id != ?
            """, (room_id, new_user_id))
            return [row[0] for row in cur.fetchall()]

def get_room_users_id(room_id: int) -> list[int]:
    """Возвращает ID участников комнаты"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM Room_Participants WHERE room_id = ?", (room_id,))
        return [row[0] for row in cur.fetchall()]
    
def get_room_id_for_user(user_id: int) -> int:
    """Возвращает ID комнаты, в которой находится пользователь"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT room_id FROM Room_Participants 
            WHERE user_id = ?
        """, (user_id,))
        result = cur.fetchone()
        return result[0] if result else None

    
def remove_participant_from_room(room_id, user_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Room_Participants
            WHERE room_id = ? AND user_id = ?
        """, (room_id, user_id))
        conn.commit()

def is_user_in_room(room_id, user_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM Room_Participants
            WHERE room_id = ? AND user_id = ?
            LIMIT 1
        """, (room_id, user_id))
        return cur.fetchone() is not None

