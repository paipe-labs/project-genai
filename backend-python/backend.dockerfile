FROM python:3.11.5-slim-bullseye

WORKDIR /backend-python/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "src/run.py"]
