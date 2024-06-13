FROM python:3.11-slim

WORKDIR /tester
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["pytest"]
