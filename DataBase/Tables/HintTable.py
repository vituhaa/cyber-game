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

#TODO: сделать функции для работы с Hint