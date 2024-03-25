FROM python:3.9-alpine

WORKDIR /genai/tests

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["pytest"]
