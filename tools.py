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

