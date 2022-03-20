import sqlite3


def connect(func):
    def wrapper(*args, **kwargs):
        con = sqlite3.connect('time.db')
        ret = func(con.cursor(), *args, **kwargs)
        con.commit()
        con.close()
        return ret

    return wrapper


@connect
def initialize_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS 
    given_time (date int, start_hour int, end_hour int, courier text)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS 
    taken_time (date int, start_hour int, end_hour int, courier text);""")


@connect
def insert_value(cur, table, values):
    # if amount of values more or less than four, then
    # VALUES(?,...) must be calculated before execution
    cur.execute(f"INSERT INTO {table} VALUES(?, ?, ?, ?)", values)


@connect
def delete_value(cur, table, conditions="date IS NOT NULL"):
    cur.execute(f"DELETE FROM {table} WHERE {conditions}")


@connect
def select_value(cur, table, conditions="date IS NOT NULL"):
    return cur.execute(f"SELECT * FROM {table} WHERE {conditions}").fetchall()
