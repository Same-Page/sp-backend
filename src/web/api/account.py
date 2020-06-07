
from api.follow import get_follower_count, get_following_count
from api.room import get_user_room_count


class Account:
    def __init__(self, token, user):
        self.token = token
        self.user = user

    def to_dict(self):
        """  
        {  
        token: "dsfaoijclkjvzcxzviojsifj"
        id: dsfa-dfad-sfasdfad-fdasfa
        numId: 123
        name: "real admin"
        about: "大家好！"
        credit: 78
        followerCount: 123
        followingCount: 321
        }
        """
        account_data = self.user

        account_data["token"] = self.token
        user_id = self.user['id']
        account_data["roomCount"] = get_user_room_count(user_id)
        account_data["followerCount"] = get_follower_count(user_id)
        account_data["followingCount"] = get_following_count(user_id)
        return account_data
