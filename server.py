import requests
import sqlite3
import tools
from time import sleep

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
def get_command(update):
    try:
        for entity in update['message']['entities']:
            if entity['type'] == 'bot_command':
                return update['message']['text']
    except KeyError:
        return False


def send_message(chat_id, text):
    requests.post(f'{api_url}/sendMessage',
                  data={'chat_id': chat_id,
                        'text': text})


# this dict is needed because /getUpdates method returns every message (aka update),
# that has been sent to a bot for a whole day
update_ids = {}
while True:
    updates = get_new_updates()
    print(updates)

    for update in updates:
        chat_id = tools.get_chat_id(update)
        update_ids[chat_id].append(update['update_id'])

        command = get_command(update)
        if not command:
            # send_message(chat_id, "Sorry, but i can't talk with you, "
            #                       "my creator is watching")
            continue

        if command == '/send_time':
            send_message(chat_id, 'Введите временной промежуточек')
            # Implement multi threading or processing solution

    sleep(1)
