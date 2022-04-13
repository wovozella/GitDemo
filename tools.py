from db_interface import select_value
from calendar import monthrange
from datetime import datetime, date
from json import dumps

api_url = f'https://api.telegram.org/bot{open(".api_token").readline()}'
now = datetime.now()
month_in_seconds = 2_592_000    # 30 days


# for avoiding not clearly raised exceptions in valid_input()
built_in_exceptions = {chr(i) for i in range(97, 123)}

days = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
        4: 'Пятница', 5: 'Суббота', 6: 'Воскресенте'}


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




def get_message(table_name, specific='IS NOT NULL'):
    """
    Format message for responding on a who take/give command
    based on relevant tables.
    "specific" argument needs for showing courier his own times to edit/delete them
    Returning message looks like that:

    05.14 (date MM.DD bold text)
    courier_name first_hour-last_hour (With link to user)
    another_courier 15-23

    05.16
    and_another_courier 8-24
    """

    user_url = ' href="tg://user?id='
    message = ''
    # creating dict with date as a key
    dates = {Date[0]: [] for Date in select_value(table_name, 'DISTINCT date',
                                                  'ORDER BY date')}
    # filling dates dict
    for Date, *details in select_value(
            table_name,
            conditions=f"WHERE user_id {specific} ORDER BY date, start_hour"):
        dates[Date].append(details)

    for Date, values in dates.items():
        times = ''
        for time in values:
            *hours, name, user_id = time
            times += f'<a{user_url}{user_id}">{name}</a> {hours[0]}-{hours[1]}\n'


        # Formatting date from YYYY-MM-DD to DD.MM
        day_in_week = date(*[int(i) for i in Date.split('-')]).weekday()
        Date = Date.split('-')
        Date = Date[1] + '.' + Date[2]

        message += f'<b>{Date} {days[day_in_week]}</b>\n' \
                   f'{times}\n'
    return message



cancel_inline_keyboard = dumps({'inline_keyboard': [[{'text': 'Отменить',
                                                      'callback_data': 'cancel'}]]})
