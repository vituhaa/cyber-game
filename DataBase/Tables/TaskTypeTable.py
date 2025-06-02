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

#TODO: написать функции для добавления типа задач и получения id по имени