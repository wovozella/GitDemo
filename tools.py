from collections.abc import Sequence
from json import dumps
import requests
api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'

# It's too complicated to easily iterate dictionaries with undefined nesting
# that has more than one key, so the chat id stores in global variable,
# which returns in another function.
# You must call only get_chat_id function
__chat_id = 0
def __extract_chat_id(dictionary):
    global __chat_id
    for key in dictionary:
        value = dictionary[key]
        if isinstance(value, dict):
            if key == 'chat':
                __chat_id = value['id']
                return
            __extract_chat_id(value)
def get_chat_id(dictionary):
    __extract_chat_id(dictionary)
    return __chat_id


def generate_inline_keyboard(keyboard: Sequence[Sequence]):
    inline_keyboard = []
    for row in keyboard:
        button_list = []
        for button in row:
            button_list.append({'text': str(button), 'callback_data': button})
        inline_keyboard.append(button_list)

    return dumps({'inline_keyboard': inline_keyboard})


# Only for testing purposes
def get_all_update_ids():
    ret = {}
    resp = requests.get(f'{api_url}/getUpdates').json()["result"]
    for update in resp:
        chat_id = get_chat_id(update)
        if chat_id not in ret:
            ret[chat_id] = []
        ret[chat_id].append(update['update_id'])
    return ret
