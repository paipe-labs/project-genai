FROM python:3.11-slim

RUN apt update && apt -y install curl

# Download Docker
ENV DOCKERVERSION=24.0.5
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
  && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKERVERSION}.tgz

# Set up the working directory
WORKDIR /cli
COPY . .

# Install additional Python app modules
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "cli.py"]

