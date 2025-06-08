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

def add_task_to_room(room_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Room_Tasks (room_id, task_id) VALUES (?, ?)", (room_id, task_id))

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
