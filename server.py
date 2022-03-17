import requests
import sqlite3
import tools
from collections.abc import Sequence
from time import sleep
from json import dumps

connection = sqlite3.connect('time.db')
cursor = connection.cursor()

# Find another way of getting api token. I guess file descriptor
# still can be opened after calling open function
api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'


def get_new_updates():
    new_updates = []
    for update in requests.get(f'{api_url}/getUpdates').json()["result"]:
        chat_id = tools.get_chat_id(update)
        # Might be rewritten
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


# returns command if there is actually a command in update
def is_command(update):
    # ENTITIES COULD BE NOT ONLY IF COMMAND WAS SENT(find a way to solve)
    if 'entities' in update['message']:
        return update['message']['text']
    return False


def send_message(chat_id, text, keyboard: Sequence[Sequence] = None):
    if keyboard:
        # Also might be optimized, maybe with some generators
        inline_keyboard = []
        for row in keyboard:
            button_list = []
            for button in row:
                button_list.append({'text': str(button), 'callback_data': button})
            inline_keyboard.append(button_list)

        keyboard = dumps({'inline_keyboard': inline_keyboard})

    requests.post(f'{api_url}/sendMessage',
                  data={'chat_id': chat_id,
                        'text': text,
                        'reply_markup': keyboard})


# this dict is needed because /getUpdates method returns every message (aka update),
# that has been sent to a bot for a whole day
update_ids = {}
while True:
    updates = get_new_updates()
    print(updates)

    for update in updates:
        chat_id = update['message']['chat']['id']
        update_ids[chat_id].append(update['update_id'])

        command = is_command(update)
        if not command:
            # send_message(chat_id, "Sorry, but i can't talk with you, "
            #                       "my creator is watching")
            continue

        if command == '/send_time':
            send_message(chat_id, 'Введите временной промежуточек',
                         keyboard=[[1, 2, 3],
                                   [4, 5, 6],
                                   [7, 8, 9],
                                   [0]])
            # Implement multi threading or processing solution

    sleep(1)
