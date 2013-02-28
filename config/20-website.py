# coding=UTF-8
'''
Initialize Web Site
'''

import os
from twisted.web.static import File
from twisted.web.server import Site
from twisted.web.resource import Resource

webroot = Resource()
log.msg('website.py: Root: %(r)s', r=webroot, logLevel=_INFO)

indexResource = File(os.path.join(csweb_home, "static", "index.html"))
webroot.putChild('', indexResource)
log.msg('website.py: Resource added at "/": %(r)s', r=indexResource, logLevel=_INFO)

faviconResource = File(os.path.join(csweb_home, "static", "img", "csweb_favicon.ico"))
webroot.putChild("favicon.ico", faviconResource)
log.msg('website.py: Resource added at "/favicon.ico": %(r)s', r=faviconResource, logLevel=_INFO)

website = Site(webroot)
log.msg('website.py: Site: %(r)s', r=webroot, logLevel=_INFO)

webport = 8080
reactor.listenTCP(webport, website)
log.msg('website.py: Site listening on port: %(p)s', p=str(webport), logLevel=_INFO)
