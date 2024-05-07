from nodes_common import local, vastai

from typing import Optional
import os
from dataclasses import dataclass


DEFAULT_DOCKER_IMAGE = os.environ.get("DEFAULT_DOCKER_IMAGE", "")
DEFAULT_PROV_SCRIPT = os.environ.get("DEFAULT_PROV_SCRIPT", "")


@dataclass
class NodeInfo:
    platform: str
    backend: str
    image: str


nodes: dict[str, NodeInfo] = {}


def create_node(
    platform: Optional[str] = None,
    backend: Optional[str] = None,
    image: Optional[str] = None,
    prov_script: Optional[str] = None,
    vastai_iid: Optional[str] = None,
) -> str:
    image = DEFAULT_DOCKER_IMAGE if image is None or image == "" else image
    prov_script = DEFAULT_PROV_SCRIPT if prov_script is None or prov_script == "" else prov_script
    if image == "":
        raise Exception(
            "No image instance passed and DEFAULT_DOCKER_IMAGE not set.")
    if prov_script == "":
        raise Exception("DEFAULT_PROV_SCRIPT environment variable not set.")

    if platform == "local":
        node_id = local.create_node(backend, image, prov_script)
    elif platform == "vastai":
        node_id = vastai.create_node(
            backend, image, prov_script, vastai_iid)
    else:
        raise Exception(f"Platform type not supported: {platform}")

    nodes[node_id] = NodeInfo(platform=platform, backend=backend, image=image)
    return node_id


def delete_node(node_id: Optional[str] = None):
    if node_id is None:
        raise ValueError("No value provided for delete_node")
    if node_id not in nodes.keys():
        raise ValueError(f"Deleting unknown node {node_id}")

    if nodes[node_id].platform == "local":
        local.delete_node(node_id)
    elif nodes[node_id].platform == "vastai":
        vastai.delete_node(node_id)
    else:
        raise Exception(
            f"Platform type not supported: {nodes[node_id].platform}")

    nodes.pop(node_id)


def list_nodes():
    return nodes
