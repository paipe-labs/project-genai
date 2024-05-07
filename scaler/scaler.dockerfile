FROM python:3.11-slim

WORKDIR /scaler
COPY scaler .
COPY nodes_common ./nodes_common

RUN pip install --no-cache-dir -r requirements.txt

ARG VASTAI_API_KEY
RUN vastai set api-key ${VASTAI_API_KEY}

ENTRYPOINT ["python", "run.py"]
