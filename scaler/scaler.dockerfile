FROM python:3.11-slim

RUN apt update && apt -y install curl

# Set up the working directory
WORKDIR /scaler
COPY scaler .
COPY nodes_common ./nodes_common

# Install additional Python app modules
RUN pip install --no-cache-dir -r requirements.txt

# Set API_KEY for vastai cli
ARG VASTAI_API_KEY
# RUN vastai set api-key ${VASTAI_API_KEY}

RUN if [[ -n ${VASTAI_API_KEY} ]]; then \
    vastai set api-key ${VASTAI_API_KEY}; \
    fi

ENTRYPOINT ["python", "run.py"]
