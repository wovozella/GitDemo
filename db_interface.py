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
def insert(cur, table, values):
    # if amount of values more or less than four, then
    # VALUES(?,...) must be calculated before execution
    cur.execute(f"INSERT INTO {table} VALUES(?, ?, ?, ?, ?)", values)


@connect
def delete(cur, table, conditions="WHERE date IS NOT NULL"):
    cur.execute(f"DELETE FROM {table} {conditions}")


@connect
def update(cur, table, time, user_id):
    date, start, end = time
    cur.execute(f"UPDATE {table} "
                f"SET start_hour={start}, end_hour={end} "
                f"WHERE user_id = {user_id} AND date = '{date}'")


@connect
def select(cur, table, columns="*", conditions="WHERE date IS NOT NULL"):
    return cur.execute(f"SELECT {columns} FROM {table} {conditions}").fetchall()


# print(select('time_to_give', conditions='WHERE date = "2022-04-30"'))
# update('time_to_give', ("2022-04-30", 8, 13), 1171601459)
# print(select('time_to_give', conditions='WHERE date = "2022-04-30"'))
