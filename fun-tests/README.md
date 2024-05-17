# Functional tests

A simple functional testing framework for `project-genai` backend server.

#### the idea

The testing setup (see `docker-compose.yml`) consists of the `backend-python` server, 5 mock nodes and a tester service.

A mock node is a web server, that provides the same interface as the [client node](https://github.com/paipe-labs/project-genai-client) but is easily manipulated by the tester service via HTTP requests: it will drop connection, fail tasks or return a valid result on command. See code in `/mock_node/main.py`.

The tester service uses `pytest` to validate servers behaviour. It sends HTTP requests to the server, acting as a user, while orchestrating the mock nodes behaviour to simulate certain scenarios. See code in `tester/test_backend.py`.

<br/><br/>
<img src="https://github.com/paipe-labs/project-genai/blob/multi-node-test/fun-tests/images/fun-tests-setup.png" alt="drawing" width="600"/>
<br/><br/>

#### Tested scenarios:

1. Even distribution of tasks among client nodes (`test_fairness`)
2. Correct handling of a client node reconnect (`test_reconnect`)
3. Handling situation with faulty / failing client nodes (`test_failing_gracefully`)
4. Even distribution of tasks and correct handling of handling many requests at once (`test_load`)
5. Handling situation with flaky connections and possibly failing nodes, managing to reschedule tasks and get them done (`test_flaky`)
6. Handling situation where all but one node are faulty and managing to reschedule tasks and get them done (`test_staying_alive`)

#### Running tests

```sh
docker compose up
```
