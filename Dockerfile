FROM python:3.7.4-alpine3.10

RUN apk --no-cache add py3-zmq libffi bash curl icu-libs openssl && pip install --upgrade pip

COPY requirements.txt /usr/local/python/

RUN apk --no-cache add --virtual build-dependencies git libffi-dev openssl-dev build-base gcc && pip install -r /usr/local/python/requirements.txt && apk del build-dependencies && rm -rf /root/.cache

COPY src /src

ENTRYPOINT ["python", "/src/main.py"]

