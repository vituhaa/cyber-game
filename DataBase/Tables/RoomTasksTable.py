import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Room_Tasks

PK  id      int
---------------
FK1 room_id int
---------------
FK2 task_id int
"""


def add_task_to_room(room_id: int, task_id: int):
    """Явная проверка параметров перед добавлением"""
    if not all(isinstance(x, int) and x > 0 for x in (room_id, task_id)):
        raise ValueError(f"Invalid IDs: room={room_id}, task={task_id}")

    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Room_Tasks (room_id, task_id)
            SELECT ?, ?
            WHERE EXISTS (SELECT 1 FROM Room WHERE id = ?)
            AND EXISTS (SELECT 1 FROM Task WHERE id = ?)
        """, (room_id, task_id, room_id, task_id))
        conn.commit()

def get_last_task_in_room(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id
            FROM Room_Tasks
            WHERE room_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (room_id,))
        result = cur.fetchone()
        return result[0] if result else None
    
def is_in_room(room_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1
            FROM Room_Tasks
            WHERE room_id = ? AND task_id = ?
            LIMIT 1
        """, (room_id, task_id))
        return cur.fetchone() is not None
