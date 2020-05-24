import json
from cfg import redis_client, chat_history_client
from common import get_room_messages


def get_content_size(key, redis_client=redis_client):
    data = redis_client.get(key)
    if not data:
        return 0

    s = len(data)/1024
    return s


def analyze_room(room_id):
    data = redis_client.get(room_id)
    if data:
        room_data = json.loads(data)
        room_size = len(room_data)/1024
        print(f'room size {room_size} kb')
        users = room_data['users']
        for u in users:
            print(f"{u['name']} connections: {len(u['connections'])}")


def get_chat_history_size(room_id):
    return get_content_size(f'chat-history-{room_id}', redis_client=chat_history_client)


print(get_content_size('news'))
analyze_room('news')
