import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Task

PK  id              int
---------------------------
    title           text
---------------------------
FK1 type_id         int
---------------------------
    difficulty      int
    ______
    1 - легкий
    2 - средний
    3 - тяжелый
---------------------------
    description     text
    __________
    описание задачи
---------------------------
    question        text
---------------------------
    correct_answer  text
---------------------------
    solution        text


"""

def get_task_by_category_and_difficulty(type_id, difficulty):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Task WHERE type_id = ? AND difficulty = ? ORDER BY RANDOM() LIMIT 1",
                    (type_id, difficulty))
        return cur.fetchone()

def get_random_task():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Task ORDER BY RANDOM() LIMIT 1")
        return cur.fetchone()

def get_hints(task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT text, penalty FROM Hint WHERE task_id = ? ORDER BY order_num ASC", (task_id,))
        return cur.fetchall()

def get_task_solution(task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT solution FROM Task WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return row[0] if row else None

def check_answer(task_id, user_answer):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT correct_answer FROM Task WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return row and row[0].strip().lower() == user_answer.strip().lower()

def create_task(title, type_id, difficulty, description, question, correct_answer, solution):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Task (title, type_id, difficulty, description, question, correct_answer, solution)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, type_id, difficulty, description, question, correct_answer, solution))
        return cur.lastrowid