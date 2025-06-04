import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect
from Tables.UserTable import update_user_score
from Tables.HintTable import get_hint_by_taskid_ordernum

"""
Task_Attempt

PK  id          int
---------------------------
FK1 task_id     int
---------------------------
FK2 user_id     int
---------------------------
    is_correct  bool
---------------------------
    used_hints  int
---------------------------
    solved_at   timestamp

"""
#TODO: перенести работу с hint в другой файл

def ensure_attempt_exists(user_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM Task_Attempt
            WHERE user_id = ? AND task_id = ?
            ORDER BY solved_at DESC LIMIT 1
        """, (user_id, task_id))
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO Task_Attempt (user_id, task_id, is_correct, used_hints, solved_at)
                VALUES (?, ?, 0, 0, ?)
            """, (user_id, task_id, datetime.utcnow()))
            return cur.lastrowid
        return row[0]

def save_attempt(user_id, task_id, is_correct, used_hints):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Task_Attempt (user_id, task_id, is_correct, used_hints, solved_at)
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, task_id, is_correct, used_hints, datetime.utcnow()))
    if is_correct:
        score = max(10, 100 - used_hints * 10)
        update_user_score(user_id, score, increment_solved=True)



def get_last_attempt(user_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT is_correct, used_hints, solved_at FROM Task_Attempt
            WHERE user_id = ? AND task_id = ?
            ORDER BY solved_at DESC LIMIT 1""",
            (user_id, task_id))
        return cur.fetchone()

def increment_used_hints(user_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        attempt_id = ensure_attempt_exists(user_id, task_id)
        cur.execute("""
            UPDATE Task_Attempt
            SET used_hints = used_hints + 1
            WHERE id = ?
        """, (attempt_id,))

def get_next_hint(user_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        # Получаем used_hints из последней попытки
        cur.execute("""
            SELECT used_hints FROM Task_Attempt
            WHERE user_id = ? AND task_id = ?
            ORDER BY solved_at DESC LIMIT 1
        """, (user_id, task_id))
        row = cur.fetchone()
        used_hints = row[0] if row else 0

        # Получаем следующую подсказку
        return get_hint_by_taskid_ordernum(task_id,used_hints+1)

def is_task_solved(user_id, task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT is_correct FROM Task_Attempt
            WHERE user_id = ? AND task_id = ?
            ORDER BY solved_at DESC LIMIT 1
        """, (user_id, task_id))
        row = cur.fetchone()
        solved = row[0] if row else 0

        if solved == 0:
            return False
        else:
            return True
