FROM python:3.11.5-slim-bullseye

WORKDIR /backend-python

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "src/run.py"]
