# Project GenAi backend server

Server part of the [project](https://paipe.io/) backend: an image generation and pipeline builder infrastructure as a service. The [client](https://github.com/paipe-labs/project-genai-client/tree/main) part of the project is linked as a submodule.

The currently used source code can be found in `backend-python/src` directory.

Apart from the server this repository also stores:
- [Scaler service](https://github.com/paipe-labs/project-genai/tree/grpc-load-balancer/scaler) - a gRPC server to create and delete new client instances
- [CLI tool](https://github.com/paipe-labs/project-genai/tree/master/genai-cli) for the same purpose

### Server

The server is an asynchronous web server built on top of [FastAPI](https://fastapi.tiangolo.com/) and [uvicorn](https://www.uvicorn.org/).
It accepts HTTP requests on image generation, saves them and the relevant metadata (we're working on [persistent storage for both users' and tasks' data in Supabase](https://github.com/paipe-labs/project-genai/issues/25)) and sends them over to client instances that satisfy or fail the request and later return the result, which is then forwarded to users. The web server is initialised in [`backend-python/src/run.py`](https://github.com/paipe-labs/project-genai/blob/master/backend-python/src/run.py)

The server and clients communicate via a two-way WebSocket connection. The connection is initiated by a client with a `register` message which contains additional metadata, and is then saved in an instance of [`Provider`](https://github.com/paipe-labs/project-genai/blob/master/backend-python/src/dispatcher/provider.py) which represents a client node. 

`Dispatcher` stores all instances of currently registered `Provider`s and is responsible for scheduling tasks (image generation requests) onto them. For more on `Dispatcher` see [`backend-python/src/dispatcher/README.md`](https://github.com/paipe-labs/project-genai/tree/master/backend-python/src/dispatcher).


### Tests

All tests use pytest, the tests that are currently integrated into the `master` branch are run for each new Pull request into `master` with the use of Github Actions. The workflows for these can be found in `.github/workflows` directory.

- [End-to-end tests](https://github.com/paipe-labs/project-genai/tree/master/tests) that test both server and client part together
	- To run: `docker compose up server node-cog-comfyui e2e-tests`
- [Unit tests](https://github.com/paipe-labs/project-genai/tree/master/backend-python/unit_tests)
	- To run: `docker compose up server-unit-tests`
- [Functional tests](https://github.com/paipe-labs/project-genai/tree/multi-node-test/fun-tests) for the server (are currently in the `multi-node-test` branch)
	- To run: `docker compose up` in the `fun-tests` directory on `multi-node-test` branch
- autopep8 linter
	- To run: `docker compose up autopep8`
