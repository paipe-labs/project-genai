# GenAI Scheduler + Dispatcher
A core module that stores tasks in a priority queue and dispatches tasks across providers.

## Installation
```pnpm i```

## Tests
```TODO: Script```


## Module concepts
### Scheduler
The entry point for all tasks. \
Each task has the parameter "How long it can stay in the queue (ms)". \
This parameter may be based on the Cost/Speed ratio. \
Then based on this parameter priority queue is sorted.


### Provider
Computation power provider. \
Each proved has meta_info. It can be public (goes from the provider itself), and private (goes from the backend, stores success ratio, etc...)

```ts
// Public meta_info
{
    _v: 1,
    installed_models: [],
    loaded_models: [],
    specifications: {
        GPU: "...",
        CPU: "...",
        RAM: "...",
    },
    network: {
        download: number,
        upload: number,
    },
    workload: {
        CPU: number,
        GPU: number,
        RAM: number,
    },
    min_cost: number,
}

```

```ts
// Private meta_info
{
    _v: 1,
    succeeded_tasks: number,
    failed_tasks: number,
    last_task: any,
    performance: {
        models: {
            [string]: {
                time: number,
                // ...
            }
        }
    }
}
```

### Dispatcher
Dispatcher gets a task from the main queue by `minimum_price`. \
Then dispatcher selects the best provider and manages a queue. \
Selecting the best provider calculates by `minimum_price` and `waiting_time`. \
We transform time to money with a coefficient `MTR` (Money Time Ratio) that exists in each task. \
If the coefficient equals 0, then we can wait an eternity but must select the cheapest provider. \
If the coefficient equals +inf, then we can't wait a second and must select the fastest provider.

If tasks failed for some executor we do the simplest thing for now – we reschedule this task with the highest priority.

### Optimizations
It seems ok to have O(N) to find the best provider, but it can be O(log(N)) with optimization structures. Such a structure can be a Li-Chao tree. It provides a query for `MTR` coefficient, returning the best provider in log(N) time.


## Higher architecture
This repository is mostly a scheduler/dispatcher logic only.
The project architecture can be divided into several parts.
- Client (Tasks executor/provider)
  - Gets orders. Makes calculations.
  - Sets minimum cost.
  - Keep-alive responses.
- Cashier (Money manager)
  - Takes orders
  - Checks user balance
  - Holds money during task execution
  - Gets receipts after execution
  - Takes commission
  - Charges a user
  - Credits a provider
- Task manager
  - Takes orders
  - Keeps tasks status updated
  - Responsible for tasks timeout and rescheduling
- Balancer (dispatcher)
  - Takes tasks
  - Manages providers and connections
  - Sends tasks to providers


---
### TODO
- [ ] Balancer
  - [ ] Unit tests for balancing metrics
  - [ ] Network websockets management
  - [ ] Protocol management (zod)
  - [ ] Rebalancing. We want providers to have the smallest queue possible, so we can balance more granularly (e.g. if a new provider appears)
- [ ] Provider stuck handling
- [ ] Tasks timeouts


