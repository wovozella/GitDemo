import sqlite3
from _thread import start_new_thread, allocate_lock
from datetime import datetime
from time import sleep


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



def db_thread():
    """
    A thread that checks records in tables for their relevance and couriers
    if they are working.
    The record edits if current time is less than start_hour by an hour. In that case
    start_hour column increases by one.
    If interval between start and end hour is 1, record deletes

    Adding new couriers and deleting fired ones implements by checking
    https://smena.samokat.ru/. It contains list of active couriers
    (Not implemented)
    """

    def edit_irrelevant_records(table):
        for row_id, user_id, date, start, end in select(
                table,
                'rowid, user_id, date, start_hour, end_hour'):

            current_time = datetime(now.year, now.month, now.day, now.hour).timestamp()
            first_hour = datetime(*[int(i) for i in date.split('-')], start).timestamp()

            if current_time > first_hour - 7200:    # 7200 - for editing an hour before current time
                if start + 1 == end:
                    delete(table, f'WHERE user_id = {user_id} AND rowid = {row_id}')
                update(table, (date, start + 1, end), user_id)


    def edit_active_couriers():
        pass


    while True:
        now = datetime.now()
        edit_irrelevant_records('time_to_give')
        edit_irrelevant_records('time_to_take')
        edit_active_couriers()
        sleep(1800)     # check every 30 minutes


start_new_thread(db_thread, ())
