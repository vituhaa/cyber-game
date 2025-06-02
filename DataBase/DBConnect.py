import sqlite3

DB_PATH = "DataBase/bot.db"

def connect():
    return sqlite3.connect(DB_PATH)

