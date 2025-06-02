import sqlite3

DB_PATH = "bot.db"

def connect():
    return sqlite3.connect(DB_PATH)

