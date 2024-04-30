import copy
import sys
sys.path.append("/backend-python/src")


from dispatcher.task import build_task_from_query, Task
from dispatcher.task_info import (
    ComfyPipelineOptions,
    StandardPipelineOptions,
    TaskOptions,
)

COMMON_TASK_ID = "1"
COMMON_TASK_DATA = {"max_cost": 15, "time_to_money_ratio": 1}


def test_task_build_standart():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    standard_pipeline_options = {
        "standard_pipeline": {
            "prompt": "space surfer",
            "model": "SD2.1",
            "size": {"height": 512, "width": 512},
            "steps": 25,
        }
    }
    task_data.update(standard_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    assert isinstance(task, Task)
    assert task.id == COMMON_TASK_ID
    assert task.max_cost == task_data["max_cost"]
    assert task.time_to_money_ratio == task_data["time_to_money_ratio"]
    assert task.task_options == TaskOptions(
        **{
            "standard_pipeline": StandardPipelineOptions(
                **standard_pipeline_options["standard_pipeline"]
            )
        }
    )


def test_task_build_comfy():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    comfy_pipeline_options = {
        "comfy_pipeline": {
            "pipelineData": "somePipeline",
            "pipelineDependencies": {"images": "imageNameToImage map"},
        }
    }
    task_data.update(comfy_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    assert isinstance(task, Task)
    assert task.id == COMMON_TASK_ID
    assert task.max_cost == task_data["max_cost"]
    assert task.time_to_money_ratio == task_data["time_to_money_ratio"]
    assert task.task_options == TaskOptions(
        **{
            "comfy_pipeline": ComfyPipelineOptions(
                **{
                    "pipeline_data": comfy_pipeline_options["comfy_pipeline"].get(
                        "pipelineData"
                    ),
                    "pipeline_dependencies": comfy_pipeline_options[
                        "comfy_pipeline"
                    ].get("pipelineDependencies"),
                }
            )
        }
    )
