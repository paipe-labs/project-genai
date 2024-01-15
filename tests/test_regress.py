import os
import requests

from loguru import logger


SERVER_URL = os.getenv("SERVER_URL")
CLIENT_HELLO_ENDPOINT = SERVER_URL + "/v1/client/hello/"
IMAGES_GENERATIONS_ENDPOINT = SERVER_URL + "/v1/images/generation/"


def test_post_client_hello():
    response = requests.post(CLIENT_HELLO_ENDPOINT)
    response_json = response.json()

    logger.info(response_json)
    assert response.status_code == 200
    assert "url" in response_json


def test_post_images_generation():
    # TODO: proper jwt token check
    input_data = {
        "token": "",
        "prompt": "space surfer",
        "steps": 25,
        "model": "SD2.1",
    }

    response = requests.post(IMAGES_GENERATIONS_ENDPOINT, json=input_data)
    response_json = response.json()

    logger.info(response_json)
    assert response.status_code == 200
    assert "result" in response_json
    assert "image" in response_json["result"]
