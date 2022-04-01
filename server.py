import requests
import tools
import db_interface as db
from time import sleep


# Find another way of getting api token. I guess file descriptor
# still can be opened after calling open function
api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'


# This list is needed because main thread of execution must not see updates,
# that processing in other threads. List must be filled with chat id in the
# beginning of thread and removed in the end
ignore_chat_ids = []

# this dict is needed because /getUpdates method returns every message (aka update),
# that has been sent to a bot for a whole day
update_ids = {}


# It's needed only for threads, so no return needed
# For proper working, every decorated function must have chat id as a first argument
def ignore_chat_id(func):
    def nested(*args):
        ignore_chat_ids.append(args[0])
        func(chat_id, args)
        ignore_chat_ids.remove(args[0])
    return nested



# default argument equals 0 because it has to be integer
def get_new_updates(specific_chat_id_updates=0):
    new_updates = []
    for update in requests.get(f'{api_url}/getUpdates').json()["result"]:
        chat_id = tools.get_chat_id(update)

        if specific_chat_id_updates:
            if specific_chat_id_updates != chat_id:
                continue

        try:
            is_value_here = update['update_id'] in update_ids[chat_id]
        except KeyError:
            # case of a new chat with bot
            update_ids[chat_id] = []
        else:
            if is_value_here:
                continue
        new_updates.append(update)
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
                        'reply_markup': keyboard})


@ignore_chat_id
def time_input_thread(chat_id, command):
    # in case of much input, just cut all updates before dialog below
    update_ids[chat_id] = tools.get_all_update_ids()[chat_id]

    while True:
        for update in get_new_updates(chat_id):
            if 'callback_query' in update:
                if update['callback_query']['data'] == 'cancel':
                    send_message(chat_id, 'Отменено')
                    return

            update_ids[chat_id].append(update['update_id'])

            valid_time = tools.valid_input(update)
            if isinstance(valid_time, tuple):
                take_or_give = command.split('_')[0][1:]
                name = update['message']['from']['first_name']
                db.insert_value(f'time_to_{take_or_give}', (*valid_time, name))

                send_message(chat_id, 'Успешно')
                return
            else:
                send_message(chat_id, f'{valid_time}\nПопробуй ещё раз')

        sleep(1)

update_ids = tools.get_all_update_ids()
while True:

    for update in get_new_updates():
        print(update)
        chat_id = tools.get_chat_id(update)
        if chat_id in ignore_chat_ids:
            continue
        update_ids[chat_id].append(update['update_id'])

        command = get_command(update)
        if not command:
            # send_message(chat_id, "Sorry, but i can't talk with you, "
            #                       "my creator is watching")
            continue

        if command in ('/give_time', '/take_time'):
            send_message(chat_id, 'Введите дату и временной промежуток в формате\n'
                                  '04.02 8-24',
                         tools.cancel_inline_keyboard)
            time_input_thread(chat_id, command)
            # Implement multi threading or processing solution

        if command in ('/who_give', '/who_take'):
            take_or_give = command.split('_')[1]
            message = db.formate_message(f'time_to_{take_or_give}')
            if not message:
                message = f'Пока что никто не делится временными'
            send_message(chat_id, message)

        if command == 'edit_my_posts':
            # show all posted time slots and allow to edit it
            pass

    sleep(0.1)
