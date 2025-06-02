import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Room

PK  id                          int
------------------------------------------
    key                         text
------------------------------------------
FK1 creator_id                  int
------------------------------------------
    status                      text
    __________
    [waiting, active, finished]
------------------------------------------
    created_at                  timestamp
------------------------------------------
    is_closed                   bool


"""

def create_room(creator_id, key):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Room (creator_id, key, status, created_at, is_closed)
            VALUES (?, ?, 'waiting', ?, 0)""",
            (creator_id, key, datetime.utcnow()))
        return cur.lastrowid

def find_open_room():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Room WHERE status = 'waiting' AND is_closed = 0 LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None


def start_game(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Room SET status = 'active' WHERE id = ?", (room_id,))



def finish_room(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Room SET status = 'finished', is_closed = 1 WHERE id = ?", (room_id,))

