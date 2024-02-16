FROM python:3.9-alpine

ENV DOCKERIZE_VERSION v0.6.1

RUN apk add curl \
    && apk add --no-cache gcc libressl-dev musl-dev libffi-dev \
    && pip install --no-cache-dir cryptography==38.0.4 \
    && apk del libressl-dev musl-dev libffi-dev \
    && wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

WORKDIR /genai/tests

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT dockerize -wait ${SERVER_URL}/v1/nodes/health/ -timeout 100s sh -c "pytest -vs --log-level=INFO"
