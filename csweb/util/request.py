# coding=UTF-8
'''
CSWeb Protocol Request parser utility.
'''

import re

class CSWPRequest():
    '''
    Basic implementation. Much more required as the requests become more complicated.
    '''
    def __init__(self, data):
        m = re.match(r"^(GET|SUB) (.*)", data)
        if m:
            self.action = m.group(1)
            self.url = m.group(2)
