FROM python:3

COPY ./petsbot /app
WORKDIR /app

RUN pip install python-telegram-bot --pre
RUN pip install redis
RUN pip install requests

CMD ["python", "-u", "/app/__main__.py"]
