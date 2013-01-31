# coding=UTF-8
'''
Initialize websocket resource.
'''

from csweb.twisted.websockets import WebSocketsResource
from csweb.service.websocket import WebSocketDeviceProtocolFactory

websocketResource = Resource()
webroot.putChild("websocket", websocketResource)
log.msg('websocket.py: Resource added at "/websocket": %(r)s', r=websocketResource, logLevel=_DEBUG)

websocketDeviceResource = WebSocketsResource(WebSocketDeviceProtocolFactory())
websocketResource.putChild("device", websocketDeviceResource)
log.msg('websocket.py: Resource added at "/websocket/device": %(r)s', r=websocketDeviceResource, logLevel=_DEBUG)
