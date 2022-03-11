import requests
import sqlite3
from time import sleep

connection = sqlite3.connect('time.db')
cursor = connection.cursor()

token = '5212534616:AAHpsQFhNQAWPgMO56CI4_jSp7O4SxKw9Q0'
base_url = 'https://api.telegram.org/bot'


def get_new_updates():
    new_updates = []
    for update in requests.get(f'{base_url}{token}/getUpdates').json()["result"]:
        chat_id = update['message']['chat']['id']
        try:
            is_value_here = update['update_id'] in update_ids[chat_id]
        except KeyError:
            update_ids[chat_id] = []
        else:
            if is_value_here:
                continue
        new_updates.append(update)
    return new_updates


# returns command if there is actually a command in update
def is_command(update):
    if 'entities' in update['message']:
        return update['message']['text']
    return False


def send_message(chat_id, text):
    requests.post(f'{base_url}{token}/sendMessage',
                  data={'chat_id': chat_id, 'text': text})


# this dict is needed because /getUpdates method returns every message (aka update),
# that has been sent to a bot for a whole day
update_ids = {}
while True:
    updates = get_new_updates()
    if updates:

        for update in updates:
            chat_id = update['message']['chat']['id']
            update_ids[chat_id].append(update['update_id'])

            command = is_command(update)
            if not command:
                # send_message(chat_id, "Sorry, but i can't talk with you, "
                #                       "my creator is watching")
                continue

            if command == '/send_time':
                resp = requests.post(f'{base_url}{token}/sendMessage',
                                     data={'chat_id': chat_id,
                                           'text': 'input a time interval to share or take',
                                           'reply_markup':
7                                               {'keyboarfddddddddddddddddddddddddddddddddddddddddddnnnnnnnnnnnnd0mufrllllllllllllllllllllllddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd5ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddhyd':
                                         8
                                                   [
                                                       [{'text': '1'}],
                                                       [{'text': '2'}],
                                                       [{'text': '3'}]
                                                   ]
                                                }
                                           })
                print(resp.text)

    sleep(1)
