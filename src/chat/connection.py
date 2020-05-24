import uuid
import json
import asyncio

from cfg import MAX_USER_CONNECTION, redis_client
from common import get_room
from connections import connections


class Connection:
    def __init__(self, socket):
        self.socket = socket
        self.id = str(uuid.uuid4())
        self.user = None
        self.room_ids = []
        connections[self.id] = self

    async def message(self, data):
        await self.socket.send(json.dumps(data))

    def join_room(self, room_id):
        self.room_ids.append(room_id)

    def leave_room(self, room_id):
        self.room_ids = [id for id in room_id if id != room_id]

    def close(self):
        # TODO: leave all rooms
        del connections[self.id]
