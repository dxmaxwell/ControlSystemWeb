# coding=UTF-8
'''
Tests for utility 'url'.
'''

from ..url import URL

from twisted.trial import unittest



class TestSchemeHTTP(unittest.TestCase):

    url = "http://www.hostname.com:8080/path/to/resource.html;hello=World&Name=Jim+Doe?name=John+Doe&Address=321+O%27Tool+Street&grade=85%25"


    def test_http(self):
        url = "http://www.hostname.com"
        self.assertEqual(str(URL(url)), url)


    def test_http_with_port(self):
        url = "http://www.hostname.com:80"
        self.assertEqual(str(URL(url)), url)


    def test_http_with_username(self):
        url = "http://username@www.hostname.com"
        self.assertEqual(str(URL(url)), url)


    def test_http_with_username_port(self):
        url = "http://username@www.hostname.com:80"
        self.assertEqual(str(URL(url)), url)


    def test_http_with_username_password_port(self):
        url = "http://username:password@www.hostname.com:80"
        self.assertEqual(str(URL(url)), url)


    def test_http_with_params_and_query(self):
        url = URL(self.url)
        self.assertEqual(url.params["hello"], "World")
        self.assertEqual(url.params["Name"], "Jim Doe")
        self.assertEqual(url.query["name"], "John Doe")
        self.assertEqual(url.query["address"], "321 O'Tool Street")
        self.assertEqual(url.query["grade"], "85%")
        url.params["Test"] = "Parameter!"
        self.assertEqual(url.params["Test"], "Parameter!")
        self.assertFalse("Test" in url.query)
        del url.params["hello"]
        self.assertFalse("hello" in url.params)
        self.assertFalse("hello" in url.query)
        url.query["Query"] = "Key=Value?"
        self.assertEqual(url.query["Query"], "Key=Value?")
        self.assertFalse("Query" in  url.params)
        del url.query["grade"]
        self.assertFalse("grade" in url.query)
        self.assertFalse("grade" in url.params)
        self.assertEqual(str(url), "http://www.hostname.com:8080/path/to/resource.html;Name=Jim+Doe&Test=Parameter%21?name=John+Doe&Address=321+O%27Tool+Street&Query=Key%3DValue%3F")


    def test_http_with_merge_params_and_query(self):
        url = URL(self.url)
        url.merge_params()
        self.assertEqual(url.params["hello"], "World")
        self.assertEqual(url.params["name"], "John Doe")
        self.assertEqual(url.params["address"], "321 O'Tool Street")
        self.assertEqual(url.params["grade"], "85%")
        self.assertEqual(url.query["hello"], "World")
        self.assertEqual(url.query["name"], "John Doe")
        self.assertEqual(url.query["address"], "321 O'Tool Street")
        self.assertEqual(url.query["grade"], "85%")
        url.params["Test"] = "Parameter!"
        self.assertEqual(url.params["Test"], "Parameter!")
        self.assertEqual(url.params["Test"], url.query["Test"])
        del url.params["hello"]
        self.assertFalse("hello" in url.params)
        self.assertFalse("hello" in url.query)
        self.assertEqual(str(url), "http://www.hostname.com:8080/path/to/resource.html?name=John+Doe&Address=321+O%27Tool+Street&grade=85%25&Test=Parameter%21")


    def test_http_with_sort_params_and_query(self):
        url = URL(self.url)
        url.merge_params()
        url.query.set_sort_keys()
        url.query["Test"] = "QueryParam!"
        url.query["zed"] = "LastOne"
        del url.query["address"]
        url.query["Attr"] = "TopRight"
        self.assertEqual(str(url), "http://www.hostname.com:8080/path/to/resource.html?Attr=TopRight&grade=85%25&hello=World&name=John+Doe&Test=QueryParam%21&zed=LastOne")
        url.query.set_lower_keys()
        url.query["UP"] = "InTheAir"
        self.assertEqual(str(url), "http://www.hostname.com:8080/path/to/resource.html?attr=TopRight&grade=85%25&hello=World&name=John+Doe&test=QueryParam%21&up=InTheAir&zed=LastOne")
        url.query.set_upper_keys()
        url.query["abc"] = "123"
        self.assertEqual(str(url), "http://www.hostname.com:8080/path/to/resource.html?ABC=123&ATTR=TopRight&GRADE=85%25&HELLO=World&NAME=John+Doe&TEST=QueryParam%21&UP=InTheAir&ZED=LastOne")


    def test_http_with_copy_params_and_query(self):
        url = URL(self.url)
        url2 = URL(url)
        self.assertEqual(str(url), str(url2))
        self.assertEqual(url.params["name"], url2.params["name"])
        self.assertEqual(url.query["name"], url2.query["name"])
        self.assertEqual(url.query["address"], url2.query["address"])
        url.merge_params()
        url3 = URL(url)
        self.assertEqual(str(url), str(url3))
        self.assertEqual(url3.params["name"], url3.query["name"])
        self.assertEqual(url3.params["address"], url3.query["address"])


class TestSchemeEPICS(unittest.TestCase):

    def setUp(self):
        URL.register_scheme("epics")


    def test_epics(self):
        url = URL("epics:PCT2026X:mA%3Afbk")
        self.assertEqual(str(url), "epics:PCT2026X:mA%3Afbk")
        url.path = URL.decode(url.path)
        self.assertEqual(str(url), "epics:PCT2026X:mA:fbk")
        url.path = URL.encode(url.path)
        self.assertEqual(str(url), "epics:PCT2026X%3AmA%3Afbk")


    def test_epics_with_parameters(self):
        url = URL("epics:PCT2026X:mA:fbk?threshold=50.0&NAME=Beam+Current")
        url.query.set_sort_keys()
        url.query.set_lower_keys()
        self.assertEqual(str(url), "epics:PCT2026X:mA:fbk?name=Beam+Current&threshold=50.0")
        url2 = URL(url)
        self.assertEqual(str(url2), "epics:PCT2026X:mA:fbk?name=Beam+Current&threshold=50.0")
        url2.query.clear()
        self.assertEqual(str(url2), "epics:PCT2026X:mA:fbk")
        url2.query["Threshold"] = url.query["Threshold"]
        url2.query["NAME"] = url.query["NAME"]
        self.assertEqual(str(url2), "epics:PCT2026X:mA:fbk?name=Beam+Current&threshold=50.0")
