FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update
RUN apt-get -y install libpq-dev gcc
RUN pip install --upgrade pip gunicorn
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY src/ /app
