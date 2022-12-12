FROM python:3-alpine

ENV UID=1000 GID=1000

COPY ./petsbot /app
COPY ./requirements.txt /app

RUN addgroup -g ${GID} petsbot \
    && adduser -h /app -s /bin/false -D -G petsbot -u ${UID} petsbot
RUN chown -R petsbot /app

USER petsbot
WORKDIR /app

RUN pip install -r /app/requirements.txt

CMD ["python", "-u", "/app/__main__.py"]
