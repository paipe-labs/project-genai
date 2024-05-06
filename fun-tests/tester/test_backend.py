import os
import httpx
import pytest
from loguru import logger
import random
import sys

logger.add(sys.stdout, format="{level} {message}")


BACKEND_ADDR = os.getenv("BACKEND_ADDR", "")
NODES_URLS = list(os.getenv("NODES_URLS", "").split())

logger.info(*NODES_URLS)

CLIENT_HELLO_ENDPOINT = BACKEND_ADDR + "/v1/client/hello/"
NODES_HEALTH_ENDPOINT = BACKEND_ADDR + "/v1/nodes/health/"

IMAGES_GENERATION_ENDPOINT = BACKEND_ADDR + "/v1/images/generation/"
TASKS_ENDPOINT = BACKEND_ADDR + "/v1/tasks/"

INPUT_DATA = {
    "token": "token",
    "comfyPipeline": {
        "pipelineData": '{"data_present": "true"}',
        "pipelineDependencies": {"images": "{'image': 'is_an_image'}"},
    },
}

RETRYING = httpx.AsyncHTTPTransport(retries=10)


async def check_healthy(url: str):
    try:
        async with httpx.AsyncClient(transport=RETRYING) as c:
            r = await c.get(url)
            assert r.status_code == 200
            resp = r.json()
            logger.info(f"OK: {resp}")
            return resp
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise e


async def generate_me_some_images(num_images=1, faulty_ok=False):
    async with httpx.AsyncClient(transport=RETRYING) as c:
        for _ in range(num_images):
            r = await c.post(IMAGES_GENERATION_ENDPOINT, json=INPUT_DATA, timeout=httpx.Timeout(12.0))
            r_json = r.json()
            try:
                logger.info(r.text)
            except:
                pass

            if faulty_ok:
                assert "error" in r_json or "ok" in r_json
                logger.info(f"Response: {r.status_code} - {r.content}")
                continue

            assert r.status_code == 202
            assert r_json["ok"] == True
            assert "images" in r_json["result"]


@pytest.mark.asyncio
async def test_fairness():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=10)) as c:
        # only do a single task
        await c.post(f"{NODES_URLS[0]}/connect",
                     params={"todo": 1})
        logger.info("ok")

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    await generate_me_some_images(1)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS[1:]:
            # only do a single task
            await c.post(f"{node_url}/connect",
                         params={"todo": 1})

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    await generate_me_some_images(len(NODES_URLS)-1)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS[1:]:
            await c.post(f"{node_url}/disconnect")


@pytest.mark.asyncio
async def test_reconnect():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=10)) as c:
        await c.post(f"{NODES_URLS[0]}/connect")

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=10)) as c:
        await c.post(f"{NODES_URLS[0]}/disconnect")

    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.get(NODES_HEALTH_ENDPOINT)
        assert r.status_code == 500

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=10)) as c:
        await c.post(f"{NODES_URLS[0]}/connect")

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=10)) as c:
        await c.post(f"{NODES_URLS[0]}/disconnect")


@pytest.mark.asyncio
async def test_failing_gracefully():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/connect", params={"connection_type": "faulty"})

    await generate_me_some_images(len(NODES_URLS), faulty_ok=True)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/connect", params={"connection_type": "flaky"})

    await generate_me_some_images(len(NODES_URLS), faulty_ok=True)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/disconnect")


@pytest.mark.asyncio
async def test_load():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    # all healthy
    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/connect", params={"todo": (99//len(NODES_URLS) + 1)})

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    await generate_me_some_images(100)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/disconnect")


@pytest.mark.asyncio
async def test_flaky():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=9)) as c:
        # healthy
        await c.post(f"{NODES_URLS[-1]}/connect")
        for node_url in NODES_URLS[0:]:
            await c.post(f"{node_url}/connect", params={"connection_type": "flaky"})

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    await generate_me_some_images(len(NODES_URLS)*4)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/disconnect")


@pytest.mark.asyncio
async def test_staying_alive():
    async with httpx.AsyncClient(transport=RETRYING) as c:
        r = await c.post(CLIENT_HELLO_ENDPOINT)
        assert r.status_code == 200
        assert "url" in r.json()

    async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=9)) as c:
        survivor = random.choice(NODES_URLS)
        await c.post(f"{survivor}/connect")
        for node_url in NODES_URLS:
            if node_url == survivor:
                continue
            await c.post(f"{node_url}/connect", params={"connection_type": "flaky", "do_fail": 0})

    resp = await check_healthy(NODES_HEALTH_ENDPOINT)
    assert resp["ok"] == True

    await generate_me_some_images(len(NODES_URLS)*4)

    async with httpx.AsyncClient(transport=RETRYING) as c:
        for node_url in NODES_URLS:
            await c.post(f"{node_url}/disconnect")
