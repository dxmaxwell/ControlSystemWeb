# coding=UTF-8
'''
Utility to help with manipulating URLs
'''

import urllib
import urlparse

from collections import Mapping, MutableMapping, OrderedDict


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


    def __init__(self, url='', scheme='', merge_params=False):
        if isinstance(url, URL):
            spliturl = url
            merge_params = url.is_merge_params() 
        else:
            spliturl = urlparse.urlparse(str(url), scheme)  
        self.scheme = spliturl.scheme
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


    def is_merge_params(self):
        return (self.params is self.query)


    def merge_params(self):
        if not self.is_merge_params():
            # Merge carefully so parameters in 'query' 
            # are not overwritten by parameters in 'params'.
            for k, v in self.params.iteritems():
                if k not in self.query:
                    self.query[k] = v
            self.params = self.query


    def _netloc(self):
        netloc = []
        if self.hostname is not None:
            if self.username is not None:
                netloc.append(self.username)
                if self.password is not None:
                    netloc.append(":")
                    netloc.append(self.password)
                netloc.append("@")
            netloc.append(self.hostname)
            if self.port is not None:
                netloc.append(":")
                netloc.append(str(self.port))
        return ''.join(netloc)


    def __str__(self):
        scheme = self.scheme
        netloc = self._netloc()
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

    def __init__(self, query='', sort_keys=False, lower_keys=False, upper_keys=False):
        MutableMapping.__init__(self)
        self._parameters = []
        self._sort_keys = sort_keys
        self._lower_keys = lower_keys
        self._upper_keys = upper_keys
        if isinstance(query, Mapping):
            if isinstance(query, _ParamMap):
                if query.is_sort_keys():
                    self.set_sort_keys()
                if query.is_lower_keys():
                    self.set_lower_keys()
                if query.is_upper_keys():
                    self.set_upper_keys()
            self.update(query)
        elif query is not None:
            self.update(OrderedDict(urlparse.parse_qsl(str(query))))


    def is_sort_keys(self):
        return self._sort_keys


    def set_sort_keys(self, sort_keys=True):
        if sort_keys:
            self._sort_keys = True
            self._parameters.sort(self._compare)


    def is_lower_keys(self):
        return self._lower_keys


    def set_lower_keys(self, lower_keys=True):
        if lower_keys:
            self._lower_keys = True
            self._upper_keys = False
            parameters = self._parameters
            self._parameters = []
            for param in parameters:
                self.__setitem__(param[0], param[1])


    def is_upper_keys(self):
        return self._upper_keys


    def set_upper_keys(self, upper_keys=True):
        if upper_keys:
            self._lower_keys = False
            self._upper_keys = True
            parameters = self._parameters
            self._parameters = []
            for param in parameters:
                self.__setitem__(param[0], param[1])


    def retain(self, key):
        if isinstance(key, (list, tuple)):
            parameters = self._parameters
            self._parameters = []
            for k in key:
                k = str(k).lower()
                for param in parameters:
                    if k == param[0].lower():
                        self.__setitem__(param[0], param[1])
        else:
            self._retain([ str(key) ])
        return


    def __getitem__(self, key):
        key = key.lower()
        for param in self._parameters:
            if key == param[0].lower():
                return param[1]
        else:
            raise KeyError() 


    def __setitem__(self, key, value):
        k = key.lower()
        if self.is_lower_keys():
            key = key.lower()
        elif self.is_upper_keys():
            key = key.upper()

        for idx in range(len(self._parameters)):
            if k == self._parameters[idx][0].lower():
                self._parameters.pop(idx)
                self._parameters.insert(idx, (key, value))
                break;
        else:
            self._parameters.append((key, value))
            if self._sort_keys:
                self._parameters.sort(self._compare)
       

    def __delitem__(self, key):
        k = key.lower()
        for idx in range(len(self._parameters)):
            if k == self._parameters[idx][0].lower():
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
        k = key.lower()
        for param in self._parameters:
            if k == param[0].lower():
                return True
        return False


    def __len__(self):
        return len(self._parameters)


    def __str__(self):
        return urllib.urlencode(self._parameters)


    def __hash__(self):
        return hash(str(self))


    def _compare(self, obj1, obj2):
        return cmp(obj1[0].lower(), obj2[0].lower())
