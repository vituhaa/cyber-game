import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
User

PK  id                  int
----------------------------
    user_tg_id          int
    ______
    id человека в тг
----------------------------
    role                text
    ____________
    user - обычный
    admin - админ
----------------------------
    name                text
----------------------------
    rating              int
----------------------------
    solved_count        int

"""

def get_or_create_user(user_tg_id, name):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM User WHERE user_tg_id = ?", (user_tg_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO User (user_tg_id, name, role, rating, solved_count) VALUES (?, ?, 'user', 0, 0)",
                    (user_tg_id, name))
        return cur.lastrowid
    
def get_username_by_tg_id(user_tg_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM User WHERE user_tg_id = ?", (user_tg_id,))
        row = cur.fetchone() 
        return row[0] if row else None
    
def update_user_score(user_tg_id, score_delta, increment_solved=False):
    with connect() as conn:
        cur = conn.cursor()
        if increment_solved:
            cur.execute("UPDATE User SET rating = rating + ?, solved_count = solved_count + 1 WHERE user_tg_id = ?",
                        (score_delta, user_tg_id))
        else:
            cur.execute("UPDATE User SET rating = rating + ? WHERE user_tg_id = ?",
                        (score_delta, user_tg_id))

def get_user_stats(user_tg_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT rating, solved_count FROM User WHERE user_tg_id = ?", (user_tg_id,))
        return cur.fetchone()
