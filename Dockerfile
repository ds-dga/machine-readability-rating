FROM python:3.9-alpine

# add psycopg2 but no larger image
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir psycopg2 \
    && apk del --no-cache .build-deps

RUN apk --no-cache add libpq

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pip install -Ur pip.txt

ENTRYPOINT [ "python", "main.py" ]