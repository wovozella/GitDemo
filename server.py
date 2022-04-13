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
def ignore_chat_id(func):
    def nested(*args):
        ignore_chat_ids[args[0]] = []
        func(chat_id, args[1:])
        ignore_chat_ids.pop(args[0])

    return nested


# default argument equals 0 because it has to be integer
def get_new_updates():
    global offset
    new_updates = []
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
    requests.post(f'{api_url}/sendMessage',
                  data={'chat_id': chat_id,
                        'text': text,
                        'reply_markup': keyboard,
                        'parse_mode': 'HTML'})


@ignore_chat_id
def time_input_thread(chat_id, command):
    command = command[0]

    while True:
        for update in ignore_chat_ids[chat_id]:
            with lock:
                ignore_chat_ids[chat_id].pop(0)
            if 'callback_query' in update:
                if update['callback_query']['data'] == 'cancel':
                    send_message(chat_id, 'Отменено')
                    return
                continue

            valid_time = tools.valid_input(update)
            if isinstance(valid_time, tuple):
                take_or_give = command.split('_')[0][1:]
                name = update['message']['from']['first_name']
                user_id = update['message']['from']['id']
                db.insert_value(f'time_to_{take_or_give}', (*valid_time, name, user_id))

                send_message(chat_id, 'Успешно')
                return
            else:
                send_message(chat_id, f'{valid_time}\nПопробуй ещё раз')

        sleep(1)


while True:

    for update in get_new_updates():
        print(update)
        chat_id = tools.get_chat_id(update)
        command = get_command(update)
        if not command:
            # send_message(chat_id, "Sorry, but i can't talk with you, "
            #                       "my creator is watching")
            continue

        if command in ('/give_time', '/take_time'):
            send_message(chat_id, 'Введите дату и временной промежуток в формате\n'
                                  '04.02 8-24',
                         tools.cancel_inline_keyboard)
            start_new_thread(time_input_thread, (chat_id, command))
            # Implement multi threading or processing solution

        if command in ('/who_give', '/who_take'):
            take_or_give = command.split('_')[1]
            message = tools.get_message(f'time_to_{take_or_give}')
            if not message:
                message = f'Пока что никто не делится временными'
            send_message(chat_id, message)

        if command == '/show_my_posts':
            # works a little wrong, it anyway shows the day when you don't have any post
            # but someone else does
            user_id = update['message']['from']['id']
            send_message(chat_id,
                         f"<u>Берёшь</u>\n{tools.get_message('time_to_take', specific=f'= {user_id}')}"
                         f"\n"
                         f"<u>Отдаёшь</u>\n{tools.get_message('time_to_give', specific=f'= {user_id}')}")

    sleep(0.1)
