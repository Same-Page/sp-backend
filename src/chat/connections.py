import uuid


connections = {

}


class Connection:
    def __init__(self, socket):
        self.socket = socket
        self.id = str(uuid.uuid4())
        self.user = None
        self.room_ids = []
        connections[self.id] = self

    def close(self):
        del connections[self.id]
