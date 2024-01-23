from __future__ import annotations

from typing import Literal

import orjson as json

from panther import status
from panther.base_websocket import Websocket, PUBSUB
from panther.db.connection import redis


class GenericWebsocket(Websocket):
    async def connect(self, **kwargs):
        """
        Check your conditions then `accept()` the connection
        """

    async def receive(self, data: str | bytes):
        """
        Received `data` of connection,
        You may want to use json.loads() on the `data`
        """

    async def send(self, data: any = None):
        """
        We are using this method to send message to the client,
        You may want to override it with your custom scenario. (not recommended)
        """
        return await super().send(data=data)


async def send_message_to_websocket(connection_id: str, data: any):
    if redis.is_connected:
        _publish_to_ws_channel(connection_id=connection_id, action='send', data=data)
    else:
        _publish_to_ws_queue(connection_id=connection_id, action='send', data=data)


async def close_websocket_connection(connection_id: str, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = ''):
    data = {
        'code': code,
        'reason': reason,
    }
    if redis.is_connected:
        _publish_to_ws_channel(connection_id=connection_id, action='close', data=data)
    else:
        _publish_to_ws_queue(connection_id=connection_id, action='close', data=data)


def _publish_to_ws_channel(connection_id: str, action: Literal['send', 'close'], data: any):
    from panther.db.connection import redis

    assert redis.is_connected, 'Redis Is Not Connected.'

    p_data = json.dumps({'connection_id': connection_id, 'action': action, 'data': data})
    redis.publish('websocket_connections', p_data)


def _publish_to_ws_queue(connection_id: str, action: Literal['send', 'close'], data: any):
    p_data = {'connection_id': connection_id, 'action': action, 'data': data}
    PUBSUB.publish(p_data)
