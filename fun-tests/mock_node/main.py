import websockets
import asyncio
import uvicorn
from loguru import logger
from fastapi import FastAPI
import json
from random import randint
import os


app = FastAPI()
BACKEND_ADDR = os.getenv("BACKEND_ADDR", "ws://localhost:8080")
PORT = int(os.getenv("PORT", 8080))
ID: int = int(os.getenv("ID", 0))


REGISTER_DATA = {
    "type": "register",
    "node_id": "",
    "metadata": {
        "models": [],
        "gpu_type": "",
        "ncpu": 0,
        "ram": 0,
    }}

RESULT_DATA = {
    "type": "result",
    "status": "ready",
    "taskId": "",
    "resultsUrl": ["url1", "url2"],
}

ERROR_DATA = {
    "type": "error",
    "status": "error",
    "taskId": "",
    "error": "Everything went wrong!",
}


CONNECTED: asyncio.Event
WS_CONNECTION: websockets.WebSocketClientProtocol | None = None


async def wsconnect(connection_type: str, todo: int, do_fail: int):
    global WS_CONNECTION
    global ID
    ID += 10
    global REGISTER_DATA
    async with websockets.connect(BACKEND_ADDR) as ws:
        WS_CONNECTION = ws
        try:
            data = REGISTER_DATA
            data["node_id"] = str(ID)
            await ws.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error in ws.send: {str(e)}")
            return

        logger.info(
            f"{ID} Connected: {connection_type}, will do: {todo}, will fail: {do_fail == 1}")
        CONNECTED.set()

        for _ in range(todo):
            try:
                response = await ws.recv()
            except Exception as e:
                logger.error(f"Error in ws.recv: {str(e)}")
                break

            if connection_type == "faulty" or \
               (connection_type == "flaky" and randint(0, 3) % 3 == 0):
                logger.info(f"{ID} Disconnected after recv...")
                break

            response_data = json.loads(response)
            task_id = response_data.get("taskId")
            if task_id is not None:
                if do_fail == 1:
                    logger.info(f"{ID} Returning error")
                    data = ERROR_DATA
                else:
                    logger.info(f"{ID} Returning result")
                    data = RESULT_DATA
                data["taskId"] = task_id

                try:
                    await ws.send(json.dumps(data))
                except Exception as e:
                    logger.error(f"Error in ws.send: {str(e)}")
                    break

    WS_CONNECTION = None
    logger.info(f"{ID} Disconnected.")


@app.post("/connect", status_code=200)
async def connected(connection_type: str = "normal", todo: int = 100, do_fail: int = 0):
    logger.info(f"{ID} RECV: connect")
    global CONNECTED
    CONNECTED = asyncio.Event()
    asyncio.create_task(
        wsconnect(connection_type=connection_type, todo=todo, do_fail=do_fail))
    await asyncio.wait_for(CONNECTED.wait(), 10)


@app.post("/disconnect", status_code=200)
async def disconnect():
    global WS_CONNECTION
    if WS_CONNECTION is not None:
        await WS_CONNECTION.close()
    logger.info(f"{ID} RECV: disconnect")


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=PORT)
