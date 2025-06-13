import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

def connect():
    return sqlite3.connect(DB_PATH)

