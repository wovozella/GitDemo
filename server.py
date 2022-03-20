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


def send_message(chat_id, text, keyboard=None):
    print(requests.post(f'{api_url}/sendMessage',
                  data={'chat_id': chat_id,
                        'text': text,
                        'reply_markup': keyboard}).json())



def time_input_thread(chat_id, command):
    ignore_chat_ids.append(chat_id)
    # in case of much input, just cut all updates before dialog below
    update_ids[chat_id] = tools.get_all_update_ids()[chat_id]

    while True:
        for update in get_new_updates():
            if tools.get_chat_id(update) == chat_id:
                update_ids[chat_id].append(update['update_id'])

                if tools.valid_input(update):
                    start_hour, end_hour = update['message']['text'].split('-')
                    if command == '/give_time':
                        send_message(chat_id, 'Успешно')

                    ignore_chat_ids.remove(chat_id)
                    return
                else:
                    send_message(chat_id, 'Некорректный ввод, попробуй ещё раз')

        sleep(1)


while True:
    updates = get_new_updates()
    # print(updates)

    for update in updates:
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

        if command == '/available_time':
            # Output an available time slots, posted by another,
            # but not the user itself
            pass

        if command == 'edit_my_posts':
            # show all posted time slots and allow to edit it
            pass

    sleep(1)
