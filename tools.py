import requests
from calendar import monthrange
from datetime import datetime, date
from json import dumps

api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'
now = datetime.now()
month_in_seconds = 2_592_000    # 30 days


# for avoiding not clearly raised exceptions in valid_input()
built_in_exceptions = {chr(i) for i in range(97, 123)}


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
        month, day = _date.split('.')

        day = int(day)
        month = int(month)
        year = now.year    # Despite user don't input year, it's necessary for database

        if 1 > month > 12:
            raise Exception('Месяц должен быть между 1 и 12')
        if 1 > day > monthrange(now.year, month)[1]:
            raise Exception('День должен быть между 1 и максимальным днём'
                            'в указанном месяце')
        if now.month == 12 and month == 1:
            year += 1

        entered_time = datetime(year, month, day).timestamp()
        current_time = datetime(now.year, now.month, now.day).timestamp()
        if entered_time - current_time > month_in_seconds:
            raise Exception('Нельзя указать часы больше чем на 30 дней вперёд')
        if entered_time - current_time < 0:
            raise Exception('Дата должна быть не меньше текущего дня')

        start = int(start)
        end = int(end)
        if day == now.day:
            if start <= now.hour:
                raise Exception('Первый час должен быть больше нынешнего часа')

        if start >= end:
            raise Exception('Последний час должен быть после первого')
        if not 8 <= start <= 23:
            raise Exception('Первый час должен быть между 8 и 23')
        if not 9 <= end <= 24:
            raise Exception('Последний час должен быть между 9 и 24')

        return date(year, month, day), start, end
    # Probably better to clearly describe all Exceptions, that may be raised
    except Exception as error:
        if set(error.args[0]).intersection(built_in_exceptions):
            return 'Некорректный или неполный ввод'
        return error.args[0]



cancel_inline_keyboard = dumps({'inline_keyboard': [[{'text': 'Cancel',
                                                      'callback_data': 'cancel'}]]})
