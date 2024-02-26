import os
import requests
import time

from loguru import logger


SERVER_URL = os.getenv("SERVER_URL")
CLIENT_HELLO_ENDPOINT = SERVER_URL + "/v1/client/hello/"
IMAGES_GENERATIONS_ENDPOINT = SERVER_URL + "/v1/images/generation/"
TASKS_ENDPOINT = SERVER_URL + "/v1/tasks/"

def wait_for_http(url: str):
    retries = 10
    exception = None
    while retries > 0:
        try:
            requests.get(url)
            return
        except requests.exceptions.ConnectionError as e:
            print(f"Got ConnectionError for url {url}: {e} , retrying")
            exception = e
            retries -= 1
            time.sleep(1)
    raise exception


def test_post_client_hello():
    wait_for_http(CLIENT_HELLO_ENDPOINT)

    response = requests.post(CLIENT_HELLO_ENDPOINT)
    response_json = response.json()

    logger.info(response_json)
    assert response.status_code == 200
    assert "url" in response_json


# def test_post_images_generation_standard():
#     wait_for_http(IMAGES_GENERATIONS_ENDPOINT)

#     # TODO: proper jwt token check
#     input_data = {
#         'token': '',
#         'standardPipeline': {
#             'prompt': 'space surfer',
#             'model': 'SD2.1',
#             'size': 512,
#             'steps': 25,
#         }
#     }
#     response = requests.post(IMAGES_GENERATIONS_ENDPOINT, json=input_data)
#     response_json = response.json()

#     logger.info(response_json)
#     assert response.status_code == 200
#     assert 'result' in response_json
#     assert 'images' in response_json['result']


def test_post_images_generation_comfyui():
    wait_for_http(IMAGES_GENERATIONS_ENDPOINT)

    # TODO: proper jwt token check

    pipelineData = """
    {
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": [
                    "10",
                    0
                ]
            },
            "class_type": "SaveImage"
        },
        "10": {
            "inputs": {
                "image": "image.png",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
    }
    """

    images = """
    {
        "image.png": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"
    }
    """

    input_data = {
        "token": "",
        "comfyPipeline": {
            "pipelineData": pipelineData,
            "pipelineDependencies": {"images": images},
        },
    }
    response = requests.post(IMAGES_GENERATIONS_ENDPOINT, json=input_data)
    response_json = response.json()

    logger.info(response_json)
    assert response.status_code == 200
    assert "result" in response_json
    assert "images" in response_json["result"]

def test_tasks_basic():
    wait_for_http(TASKS_ENDPOINT)

    # TODO: proper jwt token check

    pipelineData = """
    {
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": [
                    "10",
                    0
                ]
            },
            "class_type": "SaveImage"
        },
        "10": {
            "inputs": {
                "image": "image.png",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
    }
    """

    images = """
    {
        "image.png": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"
    }
    """

    input_data = {
        "token": "Token1",
        "comfyPipeline": {
            "pipelineData": pipelineData,
            "pipelineDependencies": {"images": images},
        },
    }
    response = requests.post(TASKS_ENDPOINT, json=input_data)
    response_json = response.json()

    logger.info(response_json)
    assert response.status_code == 201
    task_id = response_json['task_id']
    while True:

        response = requests.get(TASKS_ENDPOINT + task_id, headers={'token': 'Token1'})
        response_json = response.json()
        if response_json['status'] == 'SUCCESS':
            assert "result" in response_json
            assert "images" in response_json["result"]
            break
        assert response_json['status'] == 'PENDING'


def test_tasks_acess():
    wait_for_http(TASKS_ENDPOINT)

    # TODO: proper jwt token check

    pipelineData = """
    {
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": [
                    "10",
                    0
                ]
            },
            "class_type": "SaveImage"
        },
        "10": {
            "inputs": {
                "image": "image.png",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
    }
    """

    images = """
    {
        "image.png": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"
    }
    """

    input_data = {
        "token": "Token1",
        "comfyPipeline": {
            "pipelineData": pipelineData,
            "pipelineDependencies": {"images": images},
        },
    }
    response = requests.post(TASKS_ENDPOINT, json=input_data)
    response_json = response.json()
    task_id1 = response_json['task_id']

    input_data['token'] = 'Token2'
    response = requests.post(TASKS_ENDPOINT, json=input_data)
    response_json = response.json()
    task_id2 = response_json['task_id']

    response_valid = requests.get(TASKS_ENDPOINT + task_id1, headers={'token': 'Token1'})
    assert response_valid.status_code == 201
    
    response_invalid = requests.get(TASKS_ENDPOINT + task_id2, headers={'token': 'Token1'})
    assert response_invalid.status_code == 403
