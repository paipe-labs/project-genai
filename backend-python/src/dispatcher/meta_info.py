import typing


"""
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
    min_cost:
}
"""


class PublicMetaInfo(typing.NamedTuple):
    min_cost: int


"""
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
"""


class PrivateMetaInfo(typing.NamedTuple):
    pass
