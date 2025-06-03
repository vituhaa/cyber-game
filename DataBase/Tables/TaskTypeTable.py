import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Task_Type

PK  id          int
---------------------------
    typename    text
"""

def get_type_id_by_name(name):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Task_Type WHERE typename = ?", (name,))
        row = cur.fetchone()
        return row[0] if row else None
    
def add_task_type(name):
    with connect() as conn:
        cur = conn.cursor()
        if not get_type_id_by_name(name):
            cur.execute("""
            INSERT INTO Task_Type (typename)
            VALUES (?)""",
            (name,))
            return cur.lastrowid
    
