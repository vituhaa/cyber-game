import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect

"""
Hint

PK  id                                     int
------------------------------------------------
FK1 task_id                                int
------------------------------------------------
    text                                   text
------------------------------------------------
    order_num                              int
------------------------------------------------
    penalty                                int
    __________
    сколько снимается очков за подсказку

"""

def get_hint_by_taskid_ordernum(task_id, order_num):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
                SELECT text, penalty FROM Hint
                WHERE task_id = ? AND order_num = ?
            """, (task_id, order_num))
        return cur.fetchone()
    
def get_hints(task_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT text, penalty FROM Hint WHERE task_id = ? ORDER BY order_num ASC", (task_id,))
        return cur.fetchall()