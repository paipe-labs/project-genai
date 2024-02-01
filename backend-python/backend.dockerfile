FROM python:3.11.5-slim-bullseye

WORKDIR /genai-server

COPY . .

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python", "src/run.py"]
