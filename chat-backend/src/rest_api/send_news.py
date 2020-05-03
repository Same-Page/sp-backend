from common import get_room, get_room_messages, save_room_messages, send_msg_to_room, chat_history_client
import json
import uuid
import time

from boto3 import client as boto3_client
import boto3
import requests
import bs4
# print(os.environ.get("PYTHONPATH"))

dynamodb = boto3.resource("dynamodb")
dynamodb_client = boto3_client("dynamodb")

# 网易: https://3g.163.com
# 新闻：/touch/reconstruct/article/list/BBM54PGAwangning/0-10.html
# 娱乐：/touch/reconstruct/article/list/BA10TA81wangning/0-10.html
# 体育：/touch/reconstruct/article/list/BA8E6OEOwangning/0-10.html
# 财经：/touch/reconstruct/article/list/BA8EE5GMwangning/0-10.html
# 军事：/touch/reconstruct/article/list/BAI67OGGwangning/0-10.html
# 科技：/touch/reconstruct/article/list/BA8D4A3Rwangning/0-10.html
# 手机：/touch/reconstruct/article/list/BAI6I0O5wangning/0-10.html
# 数码：/touch/reconstruct/article/list/BAI6JOD9wangning/0-10.html
# 时尚：/touch/reconstruct/article/list/BA8F6ICNwangning/0-10.html
# 游戏：/touch/reconstruct/article/list/BAI6RHDKwangning/0-10.html
# 教育：/touch/reconstruct/article/list/BA8FF5PRwangning/0-10.html
# 健康：/touch/reconstruct/article/list/BDC4QSV3wangning/0-10.html
# 旅游：/touch/reconstruct/article/list/BEO4GINLwangning/0-10.html
# 视频：/touch/nc/api/video/recommend/Video_Recom/0-10.do?callback=videoList


topic_list = [
    "BAI6JOD9wangning",  # digital
    "BA8D4A3Rwangning",  # tech
    "BA10TA81wangning",  # recreation
    "BA8E6OEOwangning",  # sports
    "BAI6RHDKwangning",  # game
]


def get_news_by_topic(topic):
    resp = requests.get(
        f"https://3g.163.com/touch/reconstruct/article/list/{topic}/0-5.html"
    )
    data = json.loads(resp.content.decode("utf-8")[9:-1])
    return data[topic]


def get_news():
    table = dynamodb.Table("sp-news")

    used_news = table.scan(ProjectionExpression="docid",)
    used_news_ids = [news["docid"] for news in used_news["Items"]]
    used_news_set = set(used_news_ids)
    for topic in topic_list:
        news_list = get_news_by_topic(topic)
        print(topic)
        for news in news_list:
            if (
                news["docid"]
                and news["url"]
                and news["title"]
                and news["ptime"]
                and not news["docid"] in used_news_set
            ):
                print(news)

                doc_id = news["docid"]
                news["url"] = news["url"].replace("http://", "https://")
                url = news["url"]
                url_parts = url.split("/")
                if len(url_parts) < 4:
                    continue
                category = url_parts[3]
                del url_parts[3]
                url = "/".join(url_parts)
                print(category)
                # url = url.replace("3g", category)
                url = url.replace("3g", "news")
                news["constructed_url"] = url
                # print(news)
                dynamodb_client.put_item(
                    TableName="sp-news",
                    Item={
                        "partition-key": {"S": doc_id},
                        "docid": {"S": doc_id},
                        "title": {"S": news["title"]},
                        "url": {"S": news["url"]},
                        "constructed_url": {"S": news["constructed_url"]},
                        "ptime": {"S": news["ptime"]},
                    },
                )
                return [news]
    return []


def save_msg(data, room_id):
    """
    Input
        chat_message = {
            "id": message_id,
            "roomId": room_id,
            "roomType": room_type,
            "user": sender,
            "content": content
        }
    Remove roomId and roomType, add timestamp
    """
    del data['roomId']
    del data['roomType']
    data['timestamp'] = int(time.time()*1000)
    chat_history = get_room_messages(room_id)
    chat_history.append(data)
    save_room_messages(room_id, chat_history)


def get_content(url):
    headers = {
        'User-Agent': 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1)',
        'Connection': 'keep - alive',
    }
    raw_data = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(raw_data.text, 'html.parser')
    main = soup.find("article")
    title = main.find("h1", class_="title")
    # time = main.find("span", class_="time js-time").text

    content = main.find_all("div", class_="content")
    res = str(title)+str(content[0])
    res = res.replace('data-src', 'src').replace('http://', 'https://').replace('href=',
                                                                                'target="_blank" href=')
    news_id = str(uuid.uuid4())
    chat_history_client.set(news_id, res)
    return f'https://api-v3.yiyechat.com/api/news?id={news_id}'


def lambda_handler(event, context):
    news = get_news()
    if len(news) > 0:
        news = news[0]
        room_id = '45'
        room_type = 'room'

        chat_message = {
            "id": str(uuid.uuid4()),
            "roomId": room_id,
            "roomType": room_type,
            "user": {
                'id': 3,
                'name': "news",
                'about': "新闻推送",
                'avatarSrc': "https://dnsofx4sf31ab.cloudfront.net/3.jpg"
            },
            "content": {
                "type": "url",
                "dataSrc": get_content(news['url']),
                "htmlContent": '<h1>please update your extension</h1>',
                "url": news['constructed_url'],
                "title": news['title']
            }
        }

        save_msg(chat_message, room_id)

        room = get_room(room_id)
        if room:
            payload = {
                "name": "chat message",
                "data": chat_message
            }
            send_msg_to_room(
                'https://chat-v6.yiyechat.com/prod', payload, room['id'])


if __name__ == "__main__":
    lambda_handler(None, None)

    # get_content('https://3g.163.com/money/20/0309/11/F798KH6G00259DLP.html')
    # res = get_content('https://3g.163.com/digi/article/F792M9NJ001697V8.html')
    # print(res)
