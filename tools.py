import requests
from calendar import monthrange
from datetime import datetime, date
from json import dumps

api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'
now = datetime.now()
month_in_seconds = 2_592_000    # 30 days


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


def get_all_update_ids():
    ret = {}
    resp = requests.get(f'{api_url}/getUpdates').json()["result"]
    for update in resp:
        chat_id = get_chat_id(update)
        if chat_id not in ret:
            ret[chat_id] = []
        ret[chat_id].append(update['update_id'])
    return ret


def valid_input(update):
    # Comment this shit, please...
    try:
        _date, time = update['message']['text'].split(' ')
        start, end = time.split('-')
        day, month = _date.split('.')

        day = int(day)
        month = int(month)
        year = now.year    # Despite user don't input year, it's necessary for database

        if 1 > month > 12:
            raise Exception('Month must be between 1 and 12')
        if 1 > day > monthrange(now.year, month)[1]:
            raise Exception('Day must be greater than 1 and less than entered'
                            'month maximum day')
        if now.month == 12 and month == 1:
            year += 1

        entered_time = datetime(year, month, day).timestamp()
        current_time = datetime(now.year, now.month, now.day).timestamp()
        if entered_time - current_time > month_in_seconds:
            raise Exception('Date must not be greater than 30 days after'
                            'the current day')
        if entered_time - current_time < 0:
            raise Exception('Date must not be less than current day')

        start = int(start)
        end = int(end)
        if day == now.day:
            if start <= now.hour:
                raise Exception('Start hour must be greater than current hour')

        if start >= end:
            raise Exception('End hour must be greater than the start hour')
        if not 8 <= start <= 23:
            raise Exception('Start hour must be between 8 and 23')
        if not 9 <= end <= 24:
            raise Exception('End hour must be between 9 and 24')

        return date(year, month, day), start, end
    # Probably better to clearly describe all Exceptions, that may be raised
    except KeyError:
        return False


cancel_inline_keyboard = dumps({'inline_keyboard': [[{'text': 'Cancel',
                                                      'callback_data': 'cancel'}]]})
