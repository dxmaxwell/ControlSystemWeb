# coding=UTF-8
'''
Startup and configuration script for Control System Web.
'''

from epics import pv

import sys, os.path

# Setup python search path before importing modules from 'csw' #
csweb_home = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))
sys.path.append(csweb_home)

from oauth import oauth

from twisted.internet import reactor

from csweb import device
from csweb.util import log
from csweb.epics.provider import EpicsDeviceProvider

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


# Start logger with output to standard out # 

log.startLogging(sys.stdout)

log.msg('start: Home directory set: %(h)s', h=csweb_home, logLevel=_DEBUG)


# Setup Device Providers #

deviceManager = device.instance()
log.msg('start: DeviceManager: %(d)s', d=deviceManager, logLevel=_TRACE)

epicsDeviceProvider = EpicsDeviceProvider();
deviceManager.addProvider(epicsDeviceProvider)
log.msg('start: Add EpicsDeviceProvider: %(d)s', d=epicsDeviceProvider, logLevel=_TRACE)

# Setup Mail Notification #

# from csweb.service.mail import MailNotifier

# notifier = MailNotifier(("smtp.host.com", 25), "From Name <from@host.com>")
# notifier.register("epics:SR2026X:Status", "Real Name <email@host.com>")


# Setup Twitter Notification #

# from csweb.service.twitter import TwitterNotifier

# token = oauth.OAuthToken("TokenKey", "TokenSecret")
# consumer = oauth.OAuthConsumer("ConsumerKey", "ConsumerSecret")
# notifier = TwitterNotifier(consumer, token)
# notifier.register("epics:SR2026X:Status")


# Setup Web Resources #

from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.resource import Resource
from twisted.web.websockets import WebSocketsResource
from csweb.service.websocket import WebSocketDeviceProtocolFactory

root = Resource()
log.msg('start: Root Resource: %(r)s', r=root, logLevel=_TRACE)

deviceResource = Resource()
root.putChild("device", deviceResource)
log.msg('start: Resource added at "/device": %(r)s', r=deviceResource, logLevel=_DEBUG)

webSocketDeviceResource = WebSocketsResource(WebSocketDeviceProtocolFactory())
deviceResource.putChild("ws", webSocketDeviceResource)
log.msg('start: Resource added at "/device/ws": %(r)s', r=webSocketDeviceResource, logLevel=_DEBUG)

staticFileResource = File(os.path.join(csweb_home, "static"))
root.putChild("static", staticFileResource)
log.msg('start: Resource added at "/static": %(r)s', r=staticFileResource, logLevel=_DEBUG)

log.msg('start: Start listening default port: 8080', logLevel=_DEBUG)
reactor.listenTCP(8080, Site(root))

# Start the reactor #

log.msg('start: Run the reactor', logLevel=_DEBUG)
reactor.run()
