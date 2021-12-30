FROM python:3.9
# FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y vim
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pip install -U pip
RUN pip install -Ur pip.txt

ENTRYPOINT [ "python", "main.py" ]