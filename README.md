# 一叶服务器端

一叶服务器端的全部代码。

## 基本架构介绍

项目分为两个部分组成 - `/web` 与 `/chat`，两者独立运行，后者依赖前者。

### `/web` rest api 服务器

用 Python Flask 搭建的 rest api，负责一叶的所有功能，登录，注册，私信，留言，等等。

### `/chat` websocket 聊天服务器

用 Python Websocket 搭建的 websocket，负责一叶的实时聊天功能，需要调取`/web`的 API 获取用户的登录信息。

## 本地开发

### `/web` rest api 服务器

```
cd web
pip install -r requirements.txt
python run.py
```

### `/chat` websocket 聊天服务器

```
cd chat
pip install -r requirements.txt
python run.py
```

## 运行 Docker 容器

### `/web` rest api 服务器

```
cd web
docker build -t sp-web .
docker run -d --name sp-web -p 80:80 sp-web
```

### `/chat` websocket 聊天服务器

```
cd chat
docker build -t sp-chat .
docker run -d --name sp-chat -p 80:80 sp-chat
```
