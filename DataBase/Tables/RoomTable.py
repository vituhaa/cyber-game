import sys
from pathlib import Path
from datetime import datetime
import random
import string

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect
from Tables.RoomParticipants import join_room

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

#checked

def generate_random_key():
     with connect() as conn:
        cur = conn.cursor()
        characters = string.ascii_uppercase + string.digits  # A-Z и 0-9
        key = ''.join(random.choices(characters, k=6))
        cur.execute("SELECT id FROM Room WHERE key = ?",(key,))
        row = cur.fetchone()
        while row:
            key = ''.join(random.choices(characters, k=6))
            cur.execute("SELECT id FROM Room WHERE key = ?",(key,))
            row = cur.fetchone()
        return key
            
def get_room_id_by_key(key):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Room WHERE key = ?", (key,))
        return cur.fetchone()[0]

def create_room(creator_id, key, is_closed):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Room (creator_id, key, status, created_at, is_closed)
            VALUES (?, ?, 'waiting', ?, ?)""",
            (creator_id, key, datetime.utcnow(),is_closed))
    room_id = get_room_id_by_key(key)
    join_room(creator_id,room_id)
    

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

