import re

class RegType:
    PHONE = re.compile('\d{3}-\d{3}-\d{4}')
    EMAIL = re.compile('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    ADDRESS = re.compile('[a-zA-Z\s]+,\s*[a-zA-Z]+,\s*\d{5}')
