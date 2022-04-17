import sqlite3


def connect(func):
    def wrapper(*args, **kwargs):
        with sqlite3.connect('time.db') as con:
            ret = func(con.cursor(), *args, **kwargs)
        return ret

    return wrapper


@connect
def initialize_tables(cur):
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS 
        time_to_give (date date, start_hour int, end_hour int, courier text, user_id int);
    CREATE TABLE IF NOT EXISTS
        time_to_take (date date, start_hour int, end_hour int, courier text, user_id int);""")


initialize_tables()


@connect
def insert_value(cur, table, values):
    # if amount of values more or less than four, then
    # VALUES(?,...) must be calculated before execution
    cur.execute(f"INSERT INTO {table} VALUES(?, ?, ?, ?, ?)", values)


@connect
def delete_value(cur, table, conditions="date IS NOT NULL"):
    cur.execute(f"DELETE FROM {table} WHERE {conditions}")


@connect
def select_value(cur, table, columns="*", conditions="date IS NOT NULL"):
    return cur.execute(f"SELECT {columns} FROM {table} WHERE {conditions}").fetchall()
