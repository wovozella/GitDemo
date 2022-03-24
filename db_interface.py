import sqlite3
from datetime import date


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
        time_to_give (date date, start_hour int, end_hour int, courier text);
    CREATE TABLE IF NOT EXISTS
        time_to_take (date date, start_hour int, end_hour int, courier text);""")


@connect
def insert_value(cur, table, values):
    # if amount of values more or less than four, then
    # VALUES(?,...) must be calculated before execution
    cur.execute(f"INSERT INTO {table} VALUES(?, ?, ?, ?)", values)


@connect
def delete_value(cur, table, conditions="WHERE date IS NOT NULL"):
    cur.execute(f"DELETE FROM {table} {conditions}")


@connect
def select_value(cur, table, columns="*", conditions="WHERE date IS NOT NULL"):
    return cur.execute(f"SELECT {columns} FROM {table} {conditions}").fetchall()



# If you don't want to write another function, that does almost exactly
# the same, despite returning courier specific posts, then add something
# like this argument below
def formate_message(table_name, courier_specific=False):
    message = ''
    all_times = {date[0]: [] for date in select_value(table_name, 'DISTINCT date',
                                                      'ORDER BY date')}

    for date, *details in select_value(table_name, conditions="ORDER BY date, start_hour"):
        all_times[date].append(details)

    for date, values in all_times.items():
        times = ''
        for time in values:
            *hours, name = time
            times += f'{name} {hours[0]}-{hours[1]}\n'

        # Formatting date from YYYY-MM-DD to DD.MM
        date = str(date).split('-')
        date = date[2] + '.' + date[1]

        message += f'{date}\n' \
                   f'{times}\n'
    return message
