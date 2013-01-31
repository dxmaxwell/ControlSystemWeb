# coding=UTF-8
'''
Initialize websocket resource.
'''

from csweb.twisted.websockets import WebSocketsResource
from csweb.service.websocket import WebSocketDeviceProtocolFactory

websocketResource = Resource()
webroot.putChild("device", websocketResource)
log.msg('websocket.py: Resource added at "/device": %(r)s', r=websocketResource, logLevel=_DEBUG)

websocketDeviceResource = WebSocketsResource(WebSocketDeviceProtocolFactory())
websocketResource.putChild("ws", websocketDeviceResource)
log.msg('websocket.py: Resource added at "/device/ws": %(r)s', r=websocketDeviceResource, logLevel=_DEBUG)
