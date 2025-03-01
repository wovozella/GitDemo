import tools
import db_interface as db
import requests
from time import sleep
from _thread import start_new_thread, allocate_lock

lock = allocate_lock()

# Find another way of getting api token. I guess file descriptor
# still can be opened after calling open function
api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'

# value for cutting processed updates in get_new_updates()
offset = 0

# It's needed for ignoring updates in main thread and getting in another
# For proper working, every decorated function must have chat id as a first argument
ignore_chat_ids = {}


def dialog_loop(func):
    def nested(*args):
        chat_id = args[0]
        ignore_chat_ids[chat_id] = []
        func(*args)
        ignore_chat_ids.pop(chat_id)

    return nested


def get_new_updates():
    global offset
    new_updates = []

    try:
        requests.get(f'{api_url}/getUpdates',
                     data={'offset': offset}).json()["result"]
    except KeyError:  # Case of no updates
        return new_updates

    for update in requests.get(f'{api_url}/getUpdates',
                               data={'offset': offset}).json()["result"]:

        if ignore_chat_ids:
            chat_id = tools.get_chat_id(update)
            if chat_id in ignore_chat_ids:
                with lock:
                    ignore_chat_ids[chat_id].append(update)
                offset = update['update_id'] + 1
                continue

        new_updates.append(update)
    if new_updates:
        offset = new_updates[-1]['update_id'] + 1
    return new_updates


def get_command(update):
    try:
        for entity in update['message']['entities']:
            if entity['type'] == 'bot_command':
                return update['message']['text']
    except KeyError:
        return False


def send_message(chat_id, text, keyboard=None):
    return requests.post(f'{api_url}/sendMessage',
                         data={
                             'chat_id': chat_id,
                             'text': text,
                             'reply_markup': keyboard,
                             'parse_mode': 'HTML'}
                         ).json()['result']


def delete_buttons(resp):
    # resp = response.json()['result'] from sent message
    chat_id = tools.get_chat_id(resp)
    requests.post(f'{api_url}/editMessageReplyMarkup',
                  data={
                      'chat_id': chat_id,
                      'message_id': resp['message_id'],
                  })


def delete_message(resp):
    chat_id = tools.get_chat_id(resp)
    requests.post(f'{api_url}/deleteMessage',
                  data={
                      'chat_id': chat_id,
                      'message_id': resp['message_id'],
                  })


@dialog_loop
def time_replacement_thread(chat_id, table, prev_time, new_time, user_id):
    times = ''
    for time in prev_time:
        start = time[0]
        end = time[1]
        times += f'{start}-{end}\n'

    resp = send_message(chat_id, 'В этот день у тебя уже есть временные\n'
                                 f'{times}\n',
                        tools.inline_buttons([['Заменить', 'Отмена']]))

    while True:
        for update in ignore_chat_ids[chat_id]:
            with lock:
                ignore_chat_ids[chat_id].pop(0)

            if 'callback_query' in update:
                if update['callback_query']['data'] == 'Отмена':
                    delete_buttons(resp)
                    send_message(chat_id, 'Отменено')
                    return

                if update['callback_query']['data'] == 'Заменить':
                    print(*new_time)
                    db.update(table, new_time, user_id)
                    delete_buttons(resp)
                    send_message(chat_id, 'Успешно')
                    return


def time_changing_thread(chat_id, intersected_times):
    send_message(chat_id, 'Запущен поток замены')
    return


@dialog_loop
def deletion_thread(chat_id, user_id):
    callback_to_rowid = {}

    def get_users_records(table):
        ret = []
        for date, start, end, row_id in db.select(
                table, 'date, start_hour, end_hour, rowid',
                conditions=f'WHERE user_id = {user_id} ORDER BY date'):
            date = date.split('-')
            date = date[1] + '.' + date[2]
            date = f'{date} {start}-{end}'

            ret.append([date])
            callback_to_rowid[date] = row_id
        return ret

    def clear_dialog():
        delete_buttons(hint_resp)
        if to_take:
            delete_message(take_resp)
        if to_give:
            delete_message(give_resp)

    to_take = get_users_records('time_to_take')
    to_give = get_users_records('time_to_give')
    if not to_take and not to_give:
        send_message(chat_id, 'Пока что нечего удалять')
        return

    hint_resp = send_message(chat_id, 'Нажми на те временные\nкоторые хочешь удалить',
                             tools.inline_buttons([['Отмена']]))
    if to_take:
        take_resp = send_message(chat_id, 'Берёшь',
                                 tools.inline_buttons(to_take))
    if to_give:
        give_resp = send_message(chat_id, 'Отдаёшь',
                                 tools.inline_buttons(to_give))

    # code below awaits only for inline button pressing
    while True:
        for update in ignore_chat_ids[chat_id]:
            with lock:
                ignore_chat_ids[chat_id].pop(0)

            if 'callback_query' in update:
                callback = update['callback_query']['data']

                if callback == 'Отмена':
                    clear_dialog()
                    send_message(chat_id, 'Отменено')
                    return

                table = 'time_to_' + tools.del_translate[update['callback_query']['message']['text']]
                if [callback] in to_take + to_give:
                    db.delete(table, f'WHERE rowid = {callback_to_rowid[callback]}')
                    clear_dialog()
                    send_message(chat_id, 'Успешно')
                    return


@dialog_loop
def time_input_thread(chat_id, command):
    resp = send_message(chat_id, f'Введите дату и временной промежуток\n'
                                 f'который хотите {tools.input_translate[command]} в формате\n'
                                 '04.02 8-24',
                        tools.inline_buttons([['Отмена']]))

    while True:
        for update in ignore_chat_ids[chat_id]:
            with lock:
                ignore_chat_ids[chat_id].pop(0)

            if 'callback_query' in update:
                if update['callback_query']['data'] == 'Отмена':
                    delete_buttons(resp)
                    send_message(chat_id, 'Отменено')
                    return
                continue

            valid_time = tools.valid_input(update)
            if isinstance(valid_time, tuple):
                table = 'time_to_' + command[1:]
                name = update['message']['from']['first_name']
                user_id = update['message']['from']['id']

                # check if courier tries to post a time that intersect with his own posts
                intersection = tools.time_intersect(valid_time, table, user_id,
                                                    personal=True)
                if intersection:
                    start_new_thread(time_replacement_thread,
                                     (chat_id, table, intersection, valid_time, user_id))
                    return

                # reverse table name and check if there is intersection with other couriers
                table = tools.reverse_table(table)
                intersection = tools.time_intersect(valid_time, table, user_id,
                                                    personal=False)
                if intersection:
                    start_new_thread(time_changing_thread, (chat_id, intersection))
                    return
                table = tools.reverse_table(table)
                # change it back to work properly with the rest of the function

                # if no any intersections put data to db
                db.insert(table, (*valid_time, name, user_id))
                send_message(chat_id, 'Успешно')
                return
            else:
                send_message(chat_id, f'{valid_time}\nПопробуй ещё раз')

        sleep(0.1)


while True:

    for update in get_new_updates():
        print(update)
        chat_ID = tools.get_chat_id(update)
        command = get_command(update)

        if command in ('/give', '/take'):
            start_new_thread(time_input_thread, (chat_ID, command))

        if command in ('/who_give', '/who_take'):
            user_id = update['message']['from']['id']
            _take_or_give = command.split('_')[1]
            message = tools.get_message(f'time_to_{_take_or_give}', user_id)
            if not message:
                message = f'Пока что никто не делится временными'
            send_message(chat_ID, message)

        if command in ('/show', '/edit'):
            user_id = update['message']['from']['id']
            to_take = tools.get_message('time_to_take', user_id, specific=True)
            to_give = tools.get_message('time_to_give', user_id, specific=True)
            message = ''

            if not to_take and not to_give:
                message = 'Пока что ты не делишься и не берёшь часы, чтобы это сделать\n' \
                          'используй команду /give (Отдать) или /take (Взять)'
            if to_take:
                message += f"<u>Берёшь</u>\n{to_take}\n"
            if to_give:
                message += f"<u>Отдаёшь</u>\n{to_give}"

            send_message(chat_ID, message)

            if command == '/edit':
                send_message(chat_ID,
                             'Для редактирования просто заново введи временные')

        if command == '/delete':
            start_new_thread(deletion_thread, (chat_ID, update['message']['from']['id']))

    sleep(0.1)
