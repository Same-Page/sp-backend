# 一叶服务器端

一叶服务器端的全部代码。

## 基本架构介绍

项目分为两个部分组成 - `/web` 与 `/chat`，两者独立运行，后者依赖前者。

### `/web` rest api 服务器

该目录下是一个 Python Flask 应用，提供一叶所有的 rest API，支持登录，注册，私信，留言，等等功能。

### `/chat` websocket 聊天服务器

该目录下是一个 Python Websocket 应用，单独负责一叶的实时聊天功能，依赖前者提供的 rest API 来获取登录用户的信息。

## 本地开发

### `/web` rest api 服务器

```
cd web
pip install -r requirements.txt
python run.py
```

默认运行在`localhost:8080`

### `/chat` websocket 聊天服务器

```
cd chat
pip install -r requirements.txt
python run.py
```

默认运行在`localhost:8765`

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
