import sqlite3
from sqlite3 import Error
import os


def setup_db(connection, db_file):
    query_users = """
    CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegramid TEXT,
    username TEXT
    );
    """
    query_stoerung = """
    CREATE TABLE IF NOT EXISTS stoerung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    headline TEXT,
    content TEXT,
    time TEXT)"""
    execute_query(connection, query_users)
    execute_query(connection, query_stoerung)


def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path, check_same_thread=False)
        print("[SQL]        Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_query(connection, query, values=None):
    cursor = connection.cursor()
    try:
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        connection.commit()
        print("[SQL]        Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")
