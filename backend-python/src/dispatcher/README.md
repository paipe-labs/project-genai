# GenAi Dispatcher

This module is the core part of the backend server. Its main functionality is enclosed into the `Dispatcher` class. 

To allow for more performance and consistency with the web server implementation (`backend-python/src/run.py`) the module is written in asynchronous style.

### Module architecture
#### `Dispatcher` is responsible for:

1. Storing registered [client node](https://github.com/paipe-labs/project-genai-client) instances in form of `Provider` objects
2. Assigning a newly requested `Task` to the appropriate `Provider`
3. Reassigning a `Task` in case the network connection with the previously assigned `Provider` was closed / lost
4. (TBA) Creating new client nodes via gRPC calls to the Scaler service (see [Issue #48](https://github.com/paipe-labs/project-genai/issues/48)), when none are immediately available
5. (TBA) Collecting private metadata about `Provider`s (see `meta_info.py`)

#### The Scheduling Algorithm

As of now the client node instances are hosted on the same cloud provider and use the same models for generating images. Based on the currently supported workload and the choice of the pricing model (we pay the cloud host services for running client node instances irregardless of the number of requests they satisfy), the current `Dispatcher` scheduling method implementation strives to evenly balance the load of `Task`s between the `Provider`s.

With the adding of support for different providers, more variance in tasks and, as was the original idea, the support of paying to providers per image (perhaps unevenly based on the characteristics of the image request and the provider's resources) the algorithm will be updated to accommodate these changes.

See `dispatcher.py` for more details.
#### `Provider`

A class that represents [client node](https://github.com/paipe-labs/project-genai-client) instances.

Each object of the class stores
- the unique id of the client node
- an instance of the `NetworkConnection`, used for communicating with the client nodes
- a set of `Task`s currently in progress
- public (shared by the client node in time of registering in this backend server) and private (TBA: collected by `Dispatcher`) metadata.

Currently supported metadata:
- a list of downloaded generative models
- GPU type
- number of CPU cores
- RAM size

See `provider.py` and `meta_info.py` for more details.

#### `Task`

A intermediate type that represents image generation requests with additional metadata (e.g. the id of the assigned `Provider`, the scheduling status, etc).

An instance of `Task` has a scheduling status state that is changed through its lifetime.

These are the possible 6 states:

- Unscheduled (the initial state assigned at creation time)
- Scheduled
- Sent
- Aborted
- Completed
- Failed

See `task.py` and `task_info.py` for more details.

### Tests

- Unit tests: `/backend-python/unit_tests/test_dispatcher.py`
- [Functional tests](https://github.com/paipe-labs/project-genai/tree/multi-node-test/fun-tests)