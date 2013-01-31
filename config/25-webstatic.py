# coding=UTF-8
'''
Initialize static document resource.
'''

from twisted.web.static import File

staticResource = File(os.path.join(csweb_home, "static"))
webroot.putChild("static", staticResource)
log.msg('webstatic.py: Resource added at "/static": %(r)s', r=staticResource, logLevel=_DEBUG)
