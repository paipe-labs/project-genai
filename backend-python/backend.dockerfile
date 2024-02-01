FROM python:3.11.5-slim-bullseye

WORKDIR /genai-server

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "src/run.py"]
