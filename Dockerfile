FROM python:3

COPY ./petsbot /app
WORKDIR /app

RUN pip install python-telegram-bot --pre
RUN pip install redis

CMD ["python", "/app/__main__.py"]