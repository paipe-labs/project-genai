FROM python:3.11-slim

RUN apt update && apt -y install curl

WORKDIR /tester
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "main.py"]

