# coding=UTF-8
'''
Utility to help with manipulating URLs
'''

import urllib
import urlparse

from collections import MutableMapping


class URL:

    @staticmethod
    def register_scheme(scheme, uses_query=True):
        if uses_query and scheme not in urlparse.uses_query:
            urlparse.uses_query.append(scheme)


    @staticmethod
    def decode(s):
        return urllib.unquote(s)


    @staticmethod
    def encode(s):
        return urllib.quote(s)


    def __init__(self, url, scheme='', merge_params=False):
        spliturl = urlparse.urlparse(url, scheme)
        self.scheme = spliturl.scheme
        self.netloc = spliturl.netloc
        self.path = spliturl.path
        self.params = _ParamMap(spliturl.params)
        self.query = _ParamMap(spliturl.query)
        self.fragment = spliturl.fragment
        self.username = spliturl.username
        self.password = spliturl.password
        self.hostname = spliturl.hostname
        self.port = spliturl.port
        if merge_params:
            self.merge_params()


    def merge_params(self):
        if self.params is not self.query:
            self.query.update(self.params)
            self.params = self.query


    def __str__(self):    
        scheme = self.scheme
        netloc = self.netloc
        path = self.path
        if self.params is self.query:
            params = ''
            query = str(self.query)
        else:
            params = str(self.params)
            query = str(self.query)
        fragment = self.fragment
        return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))


    def __hash__(self):
        return hash(str(self))


    def __eq__(self, obj):
        return (str(self) == obj)


class _ParamMap(MutableMapping):

    def __init__(self, query, sort_keys=False, lower_keys=False, upper_keys=False):
        self._parameters = []
        self._sort_keys = sort_keys
        self._lower_keys = lower_keys
        self._upper_keys = upper_keys
        self.update(query)


    def set_sort_keys(self, sort_keys=True):
        if sort_keys:
            self._sort_keys = True
            self._parameters.sort(self._compare)


    def set_lower_keys(self, lower_keys=True):
        if lower_keys:
            self._lower_keys = True
            self._upper_keys = False
            parameters = self._parameters
            self._parameters = []
            for param in parameters:
                self.__setitem__(param[0], param[1])


    def set_upper_keys(self, upper_keys=True):
        if upper_keys:
            self._lower_keys = False
            self._upper_keys = True
            parameters = self._parameters
            self._parameters = []
            for param in parameters:
                self.__setitem__(param[0], param[1])


    def update(self, obj):
        if isinstance(obj, basestring):
            params = urlparse.parse_qsl(obj)
            return MutableMapping.update(self, params)
        return MutableMapping.update(self, obj)


    def retain(self, key):
        parameters = self._parameters
        self._parameters = []
        if isinstance(key, basestring):
            if self._lower_keys:
                key = key.lower()
            elif self._upper_keys:
                key = key.upper()
            for param in parameters:
                if key == param[0]:
                    self.__setitem__(param[0], param[1])
            return
        for k in key:
            if self._lower_keys:
                k = k.lower()
            elif self._upper_keys:
                k = k.upper()
            for param in parameters:
                if k == param[0]:
                    self.__setitem__(param[0], param[1])
        return


    def __getitem__(self, key):
        if self._lower_keys:
            key = key.lower()
        elif self._upper_keys:
            key = key.upper()
        for param in self._parameters:
            if key == param[0]:
                return param[1]
        else:
            raise KeyError() 


    def __setitem__(self, key, value):
        if self._lower_keys:
            key = key.lower()
        elif self._upper_keys:
            key = key.upper()
        for idx in range(len(self._parameters)):
            if key == self._parameters[idx][0]:
                self._parameters.pop(idx)
                self._parameters.insert(idx, (key, value))
                break;
        else:
            self._parameters.append((key, value))
            if self._sort_keys:
                self._parameters.sort(self._compare)
       

    def __delitem__(self, key):
        if self._lower_keys:
            key = key.lower()
        elif self._upper_keys:
            key = key.upper()
        for idx in range(len(self._parameters)):
            if key == self._parameters[idx][0]:
                self._parameters.pop(idx)
                break;
        else:
            raise KeyError()


    def __iter__(self):
        keys = []
        for param in self._parameters:
            keys.append(param[0])
        return keys.__iter__()


    def __contains__(self, key):
        if self._lower_keys:
            key = key.lower()
        elif self._upper_keys:
            key = key.upper()
        for param in self._parameters:
            if key == param[0]:
                return True
        return False


    def __len__(self):
        return len(self._parameters)


    def __str__(self):
        return urllib.urlencode(self._parameters)


    def __hash__(self):
        return hash(str(self))


    def _compare(self, obj1, obj2):
        return cmp(obj1[0], obj2[0])
