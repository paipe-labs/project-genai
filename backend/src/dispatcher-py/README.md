# GenAi Dispatcher

Core module for storing and scheduling tasks (dispatching across providers)

### Tests

TODO

### Module architecture

#### Task

TODO

See code in:
- `task.py`
- `task_info.py`

#### Dispatcher
Dispatcher stores tasks in the inner `EntryQueue`

TODO: research a better way to schedule tasks

See code in:
- `dispatcher.py`
- `entry_queue.py`: the original code used a min heap, but it seemed to work with the heap data as if it were sorted, so current version uses a list sorted in descending order according to task's priority.

#### Provider
A computation power provider. Each provider has public and private meta info, that represent the characteristics of the machine used in scheduling tasks.

`ProviderEstimator`class member of each `Provider` is used to predict the time needed to complete the currently scheduled tasks.

See code in:
- `provider.py`
- `provider_estimator.py`
- `meta_info.py`

Public meta_info:
```json
{
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

Private meta_info:
```json
{
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

#### Network connection

TODO

See code in:
- `network_connection.py`

