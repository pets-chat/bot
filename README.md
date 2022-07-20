# /pets/ bot

This is our Telegram Bot. More information to follow.

## Rapid development with docker locally.

By default, the Dockerfile will bundle the files into one single image. For production, this is good, however for
development it means re-building the container each time. Rename `docker-compose.dev.yml` to `docker-compose.override.yml`
to override this behaviour and use Dockervolumes.