FROM tiangolo/uwsgi-nginx-flask:python3.8
RUN apt-get update && apt-get install -y ca-certificates

COPY . /app

RUN pip install -r requirements.txt