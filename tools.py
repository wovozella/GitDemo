import requests
from json import dumps

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


def valid_time_input(update):
    try:
        start, end = update['message']['text'].split('-')
        start = int(start)
        end = int(end)
        if start >= end:
            raise Exception('End hour must be greater than the start hour')
        if not 8 <= start <= 23:
            raise Exception('Start hour must be between 8 and 23')
        if not 9 <= end <= 24:
            raise Exception('End hour must be between 9 and 24')
        return True
    except Exception:
        return False


cancel_inline_keyboard = dumps({'inline_keyboard': [[{'text': 'Cancel',
                                                      'callback_data': 'cancel'}]]})
