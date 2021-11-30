FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pip install -U pip
RUN pip install -Ur pip.txt

ENTRYPOINT [ "python", "main.py" ]