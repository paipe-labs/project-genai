FROM python:3.11.5-slim-bullseye

RUN pip install \
      autopep8==2.1.0

# use your own entrypoint in docker-compose