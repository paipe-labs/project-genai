FROM python:3.11-slim

WORKDIR /tests

COPY tests .
COPY proto ./proto

RUN pip install --no-cache-dir -r requirements.txt

ARG VASTAI_API_KEY
RUN vastai set api-key ${VASTAI_API_KEY}

ENTRYPOINT ["pytest"]

